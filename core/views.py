from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.crypto import get_random_string
import json
import threading
import time
import socket
import re

# Almacén de salas en memoria seguro para hilos (Thread-Safe In-Memory Room Store)
# ponytail: Diccionario simple protegido con Lock() en lugar de caché volátil sin transaccionalidad
ROOMS = {}
ROOMS_LOCK = threading.Lock()

def get_lan_ip():
    """Detecta la IP real de esta máquina en la red local (Wi-Fi/LAN)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def clean_expired_rooms():
    """Elimina salas inactivas con más de 2 horas de antigüedad."""
    now = time.time()
    with ROOMS_LOCK:
        expired = [rid for rid, r in ROOMS.items() if now - r.get('created', 0) > 7200]
        for rid in expired:
            del ROOMS[rid]

def home(request):
    return render(request, 'core/index.html')

@csrf_exempt
def create_room(request):
    clean_expired_rooms()
    # Generar código de sala estrictamente en MAYÚSCULAS y dígitos sin caracteres ambiguos (0, O, 1, I)
    room_id = get_random_string(6, allowed_chars='ABCDEFGHJKLMNPQRSTUVWXYZ23456789').upper()
    
    server_ip = get_lan_ip()
    host = request.get_host()
    port = host.split(':')[1] if ':' in host else '8000'
    server_host = f"{server_ip}:{port}" if port else server_ip

    with ROOMS_LOCK:
        ROOMS[room_id] = {
            'created': time.time(),
            'messages': []
        }

    return JsonResponse({
        'room_id': room_id,
        'server_ip': server_ip,
        'server_host': server_host
    })

@csrf_exempt
def signal(request, room_id):
    room_id = room_id.strip().upper()

    with ROOMS_LOCK:
        if room_id not in ROOMS:
            ROOMS[room_id] = {
                'created': time.time(),
                'messages': []
            }
        room = ROOMS[room_id]

    if request.method == 'POST':
        try:
            payload = json.loads(request.body)
            client_ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '')).split(',')[0].strip()
            # Si el emisor está en localhost/loopback, su IP en la LAN es la del servidor
            effective_ip = client_ip if (client_ip and client_ip not in ('127.0.0.1', '::1', 'localhost')) else get_lan_ip()

            # Reemplazar hostnames mDNS .local por la IP real en la red local
            if payload.get('type') == 'candidate' and 'candidate' in payload:
                cand = payload['candidate']
                if isinstance(cand, dict) and 'candidate' in cand and effective_ip:
                    cand['candidate'] = re.sub(r'[\w.-]+\.local', effective_ip, cand['candidate'])
                elif isinstance(cand, str) and effective_ip:
                    payload['candidate'] = re.sub(r'[\w.-]+\.local', effective_ip, cand)
            elif payload.get('type') in ['offer', 'answer']:
                obj = payload.get(payload.get('type'), {})
                if isinstance(obj, dict) and 'sdp' in obj and effective_ip:
                    obj['sdp'] = re.sub(r'[\w.-]+\.local', effective_ip, obj['sdp'])
                    obj['sdp'] = re.sub(r'c=IN IP4 0\.0\.0\.0', f'c=IN IP4 {effective_ip}', obj['sdp'])

            with ROOMS_LOCK:
                msg_id = len(room['messages']) + 1
                payload['id'] = msg_id
                room['messages'].append(payload)

            return JsonResponse({'status': 'ok', 'id': msg_id, 'effective_ip': effective_ip})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    # GET: Sondeo de mensajes sin borrado destructivo
    sender = request.GET.get('sender')
    try:
        after_id = int(request.GET.get('after', 0))
    except ValueError:
        after_id = 0

    with ROOMS_LOCK:
        all_msgs = list(room['messages'])
        if sender:
            to_return = [m for m in all_msgs if m.get('sender') != sender and m.get('id', 0) > after_id]
        else:
            to_return = [m for m in all_msgs if m.get('id', 0) > after_id]

    return JsonResponse({'messages': to_return, 'room_id': room_id})

from django.conf import settings

def manifest(request):
    manifest_path = settings.BASE_DIR / 'static' / 'manifest.json'
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type="application/manifest+json")
    except FileNotFoundError:
        return JsonResponse({"error": "Manifest not found"}, status=404)

def sw(request):
    sw_path = settings.BASE_DIR / 'static' / 'sw.js'
    try:
        with open(sw_path, 'r', encoding='utf-8') as f:
            content = f.read()
        response = HttpResponse(content, content_type="application/javascript")
        response['Service-Worker-Allowed'] = '/'
        return response
    except FileNotFoundError:
        return HttpResponse("// SW not found", content_type="application/javascript", status=404)