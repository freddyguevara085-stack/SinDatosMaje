# 📝 SinDatosMaje

> **Transferencia de archivos directa P2P para el aula sin internet y con cero consumo de datos.**

**SinDatosMaje** es una Progressive Web App (PWA) diseñada para escuelas y universidades donde el acceso a internet es limitado, inestable o inexistente. Permite a docentes y estudiantes compartir fotos de apuntes, documentos PDF y archivos directamente entre laptops y teléfonos móviles a través de la red Wi-Fi local o un punto de acceso (hotspot), sin consumir un solo mega de datos móviles y sin que los archivos pasen por ningún servidor externo.

---

## 🚀 Características Principales

* 📶 **100% Offline en Red Local (LAN):** No requiere internet. Funciona conectado a cualquier router Wi-Fi o al punto de acceso (zona Wi-Fi) de un celular sin plan de datos.
* ⚡ **Transferencia Par a Par (P2P con WebRTC):** Los dispositivos se conectan directamente mediante RTCDataChannel. Las transferencias aprovechan la velocidad completa de la red Wi-Fi local (50 - 300 Mbps).
* 🔒 **Privacidad Total:** Los archivos **nunca se suben al servidor** ni tocan internet. La laptop solo actúa como intermediario de señalización inicial (handshake) y proveedor del App Shell.
* 📱 **PWA Instalable:** Cuenta con Service Worker con estrategia *Cache-First* y manifest.json. Se puede instalar como aplicación nativa en Android, iOS o Windows.
* 📦 **Cero Dependencias de CDNs:** Todos los recursos (Tailwind CSS, escáner de QR, generador de QR y fuentes) se sirven localmente desde el proyecto.
* 🎨 **Estilo Sketch-Note (Libreta Escolar):** Interfaz visual orgánica con diseño de libreta rayada, trazos dibujados a mano, tipografía *Patrick Hand* y metadatos en *JetBrains Mono*.

---

## 🛠️ Arquitectura Técnica

`	ext
[ Emisor (Laptop / Celular) ]                            [ Receptor (Celular / Laptop) ]
           │                                                            │
           │  1. Arrastra archivo -> POST /api/create-room/             │
           ├──────────────────────────────┐                             │
           │                              ▼                             │
           │                     [ Servidor Django ]                    │
           │                     (Señalización en RAM)                  │
           │                              ▲                             │
           │  2. Muestra QR con URL LAN   │  3. Escanea QR / Código     │
           │     y oferta SDP inicial     │     y envía respuesta SDP   │
           ├─────────────────────────────►│◄────────────────────────────┤
           │                              │                             │
           │  4. Enlace P2P establecido directamente vía Wi-Fi local    │
           ▼════════════════════════════════════════════════════════════▼
                    WebRTC RTCDataChannel (Chunks de 32 KB)
                    Velocidad LAN directa - Cero uso de datos
`

### Componentes Clave:
1. **Señalización Ligera en Django (core/views.py):**
   * Diccionario thread-safe en memoria con 	hreading.Lock().
   * Normalización automática de códigos de sala en mayúsculas (ABCDEFGHJKLMNPQRSTUVWXYZ23456789) para evitar discrepancias al escribir en pantallas táctiles.
   * Auto-descubrimiento de la IP local de la tarjeta de red (192.168.1.X).
   * **Reescritura de mDNS .local:** En redes locales sin internet, los navegadores Chromium anonimizan las IPs bajo nombres .local que los móviles Android no pueden resolver. El backend traduce automáticamente estos nombres a la IP LAN real del emisor en los candidatos ICE y SDP.
2. **Motor WebRTC en Cliente (core/template/core/index.html):**
   * Fragmentación del archivo en trozos de 32 KB utilizando FileReader y ArrayBuffer.
   * Control de saturación y memoria mediante ufferedAmountLowThreshold.
   * Reensamblado reactivo y descarga automática/manual mediante Blob y URL.createObjectURL.
3. **App Shell Offline (static/sw.js):**
   * Service Worker con estrategia *Cache-First* para HTML, JS, CSS y fuentes locales.
   * Exclusión estricta de rutas dinámicas de señalización (/api/*) para asegurar que el handshake siempre viaje en vivo.

---

## 📂 Estructura del Proyecto

`	ext
SinDatosMaje/
├── config/                  # Configuración del proyecto Django (settings, urls, wsgi)
├── core/                    # Aplicación principal
│   ├── template/core/       # Plantilla principal index.html (Sketch-Note UI)
│   ├── views.py             # Señalización WebRTC, PWA handlers y vistas
│   └── urls.py              # Rutas de señalización (/api/) y PWA (/sw.js, /manifest.json)
├── static/                  # Recursos estáticos 100% locales (sin CDNs)
│   ├── css/fonts.css        # Declaraciones @font-face locales
│   ├── fonts/               # Archivos woff2 de Patrick Hand y JetBrains Mono
│   ├── icons/               # Íconos PWA (SVG, 192x192 PNG, 512x512 PNG)
│   ├── vendor/              # Librerías locales (tailwind.js, qrcode.min.js, html5-qrcode.min.js)
│   ├── manifest.json        # Manifiesto Web de la PWA
│   └── sw.js                # Service Worker con estrategia Cache-First
├── manage.py                # Gestor de Django
└── README.md
`

---

## 🚀 Guía de Inicio Rápido

### 1. Requisitos
* Python 3.10 o superior.
* Django 5 o superior (pip install django).

### 2. Configuración y Ejecución
1. Clona o descarga el repositorio:
   `ash
   git clone <url-del-repositorio>
   cd SinDatosMaje
   `
2. Activa tu entorno virtual (si aplica):
   `ash
   # En Windows:
   venv\Scripts\activate
   # En Linux / macOS:
   source venv/bin/activate
   `
3. Inicia el servidor escuchando en todas las interfaces de red local:
   `ash
   python manage.py runserver 0.0.0.0:8000
   `

---

## 👨‍🏫 Guía de Uso en el Aula

1. **Conexión de Red:**
   * Conecta tu laptop y los celulares de los alumnos a la misma red Wi-Fi (o crea una **Zona Wi-Fi / Hotspot** desde un teléfono móvil, sin necesidad de tener internet o saldo).
2. **Abrir la Aplicación:**
   * En la laptop, abre el navegador en: http://localhost:8000/ (o la IP que reporte la consola, ej: http://192.168.1.7:8000/).
3. **Enviar un Archivo (Profesor / Emisor):**
   * Arrastra o selecciona una foto, apunte o PDF en la zona de dibujo.
   * La aplicación generará automáticamente un código de sala y un código QR con la IP local de tu equipo.
4. **Recibir el Archivo (Alumno / Receptor):**
   * El alumno apunta su cámara al código QR (o escribe el código de 6 letras desde el botón de escaneo).
   * La conexión P2P se establecerá de forma instantánea y el archivo se descargará en su dispositivo sin gastar un solo megabyte.

---

## 📋 Consejos de Compatibilidad en Red Local

* **Cámara en HTTP:** Los navegadores modernos bloquean el acceso a la cámara web a través de direcciones IP por HTTP plano (http://192.168.1.X). Si el escáner muestra la pantalla negra en el móvil, el alumno puede:
  1. Usar la cámara predeterminada de su teléfono para escanear el QR.
  2. O ingresar manualmente el código de 6 letras en el recuadro provisto.
* **Tamaño de Archivo Seguro:** Recomendado para apuntes, presentaciones, fotos y PDFs de hasta **200 MB** para garantizar un uso óptimo de memoria RAM en teléfonos móviles.

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Desarrollado con ❤️ para facilitar el acceso a la educación y el intercambio de conocimiento sin barreras de conectividad.
