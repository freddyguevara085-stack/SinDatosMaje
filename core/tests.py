from django.test import TestCase, Client
import json
import time
from core.views import ROOMS, ROOMS_LOCK

class SignalingTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Ensure rooms dictionary is clean for isolation
        with ROOMS_LOCK:
            ROOMS.clear()

    def test_create_room(self):
        response = self.client.post('/api/create-room/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('room_id', data)
        self.assertEqual(len(data['room_id']), 6)
        self.assertIn('server_ip', data)

    def test_signaling_flow_and_isolation(self):
        # Create two rooms
        res_a = self.client.post('/api/create-room/')
        room_id_a = res_a.json()['room_id']
        res_b = self.client.post('/api/create-room/')
        room_id_b = res_b.json()['room_id']

        # Offerer posts offer to room A
        offer_payload = {
            'sender': 'offerer',
            'type': 'offer',
            'offer': {'type': 'offer', 'sdp': 'v=0\r\ntest'}
        }
        res_offer = self.client.post(f'/api/signal/{room_id_a}/', data=json.dumps(offer_payload), content_type='application/json')
        self.assertEqual(res_offer.status_code, 200)

        # Answerer polls room A and receives offer
        poll_res_a = self.client.get(f'/api/signal/{room_id_a}/?sender=answerer&after=0')
        msgs_a = poll_res_a.json().get('messages', [])
        self.assertEqual(len(msgs_a), 1)
        self.assertEqual(msgs_a[0]['type'], 'offer')
        
        # Polling again with 'after' ID returns empty list
        after_id = msgs_a[0]['id']
        poll_res_after = self.client.get(f'/api/signal/{room_id_a}/?sender=answerer&after={after_id}')
        self.assertEqual(len(poll_res_after.json().get('messages', [])), 0)

        # Room B remains empty
        poll_res_b = self.client.get(f'/api/signal/{room_id_b}/?sender=answerer&after=0')
        self.assertEqual(len(poll_res_b.json().get('messages', [])), 0)

    def test_invalid_json(self):
        res = self.client.post('/api/create-room/')
        room_id = res.json()['room_id']
        res_err = self.client.post(f'/api/signal/{room_id}/', data='not-json', content_type='application/json')
        self.assertEqual(res_err.status_code, 400)
        self.assertEqual(res_err.json()['error'], 'Invalid JSON')

    def test_mDNS_replacement_in_sdp(self):
        res = self.client.post('/api/create-room/')
        room_id = res.json()['room_id']

        payload = {
            'sender': 'offerer',
            'type': 'offer',
            'offer': {'type': 'offer', 'sdp': 'c=IN IP4 0.0.0.0\r\na=candidate:1 1 UDP 2130706431 test.local 50000 typ host'}
        }
        self.client.post(f'/api/signal/{room_id}/', data=json.dumps(payload), content_type='application/json')
        
        # Test replacing IP
        poll_res = self.client.get(f'/api/signal/{room_id}/?after=0')
        msgs = poll_res.json().get('messages', [])
        sdp = msgs[0]['offer']['sdp']
        # 0.0.0.0 and .local should be replaced by actual IP (127.0.0.1 since we test via loopback)
        self.assertNotIn('0.0.0.0', sdp)
        self.assertNotIn('test.local', sdp)

    def test_expired_rooms_cleanup(self):
        with ROOMS_LOCK:
            ROOMS['OLDROOM'] = {'created': time.time() - 8000, 'messages': []}
            ROOMS['NEWROOM'] = {'created': time.time(), 'messages': []}
        
        # create_room triggers clean_expired_rooms
        self.client.post('/api/create-room/')
        
        with ROOMS_LOCK:
            self.assertNotIn('OLDROOM', ROOMS)
            self.assertIn('NEWROOM', ROOMS)

class CoreViewsTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_home_page(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        self.assertIn('Modo Offline Puro', content)
        self.assertIn('Modo Aula', content)

    def test_manifest_and_sw(self):
        # We ensure they don't crash. Depending on STATIC_ROOT they might return 200 or 404
        res_manifest = self.client.get('/manifest.json')
        self.assertIn(res_manifest.status_code, [200, 404])
        
        res_sw = self.client.get('/sw.js')
        self.assertIn(res_sw.status_code, [200, 404])
