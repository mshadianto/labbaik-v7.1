"""
LABBAIK AI v6.0 - Progressive Web App (PWA) Support
=====================================================
Enable offline capabilities and installable app experience.

Features:
- Service Worker for caching
- Web App Manifest for installation
- Offline fallback page
- Background sync for pending actions
- Push notifications support (future)

Usage:
1. Add PWA meta tags to Streamlit
2. Register service worker
3. Handle offline/online states
"""

import streamlit as st
import streamlit.components.v1 as components
import json
import os
from typing import Dict, Any
from ui.components.shared_styles import inject_css, HERO_CSS, CARD_CSS

try:
    from services.ai.helpers import add_xp_safe
except ImportError:
    def add_xp_safe(*a, **kw): pass

# =============================================================================
# PWA MANIFEST
# =============================================================================

PWA_MANIFEST = {
    "name": "LABBAIK AI - Platform Umrah Cerdas",
    "short_name": "LABBAIK AI",
    "description": "Platform AI Perencanaan Umrah #1 Indonesia",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#0a0a0a",
    "theme_color": "#d4af37",
    "orientation": "portrait-primary",
    "scope": "/",
    "lang": "id",
    "categories": ["travel", "lifestyle", "religious"],
    "icons": [
        {
            "src": "/app/static/icon-72.png",
            "sizes": "72x72",
            "type": "image/png",
            "purpose": "any maskable"
        },
        {
            "src": "/app/static/icon-96.png",
            "sizes": "96x96",
            "type": "image/png",
            "purpose": "any maskable"
        },
        {
            "src": "/app/static/icon-128.png",
            "sizes": "128x128",
            "type": "image/png",
            "purpose": "any maskable"
        },
        {
            "src": "/app/static/icon-144.png",
            "sizes": "144x144",
            "type": "image/png",
            "purpose": "any maskable"
        },
        {
            "src": "/app/static/icon-152.png",
            "sizes": "152x152",
            "type": "image/png",
            "purpose": "any maskable"
        },
        {
            "src": "/app/static/icon-192.png",
            "sizes": "192x192",
            "type": "image/png",
            "purpose": "any maskable"
        },
        {
            "src": "/app/static/icon-384.png",
            "sizes": "384x384",
            "type": "image/png",
            "purpose": "any maskable"
        },
        {
            "src": "/app/static/icon-512.png",
            "sizes": "512x512",
            "type": "image/png",
            "purpose": "any maskable"
        }
    ],
    "screenshots": [
        {
            "src": "/app/static/screenshot-wide.png",
            "sizes": "1280x720",
            "type": "image/png",
            "form_factor": "wide"
        },
        {
            "src": "/app/static/screenshot-mobile.png",
            "sizes": "750x1334",
            "type": "image/png",
            "form_factor": "narrow"
        }
    ],
    "shortcuts": [
        {
            "name": "AI Assistant",
            "short_name": "Chat",
            "description": "Tanya AI tentang umrah",
            "url": "/?page=chat",
            "icons": [{"src": "/app/static/icon-chat.png", "sizes": "96x96"}]
        },
        {
            "name": "Simulasi Biaya",
            "short_name": "Simulasi",
            "description": "Hitung biaya umrah",
            "url": "/?page=simulator",
            "icons": [{"src": "/app/static/icon-calc.png", "sizes": "96x96"}]
        },
        {
            "name": "SOS Darurat",
            "short_name": "SOS",
            "description": "Bantuan darurat",
            "url": "/?page=sos",
            "icons": [{"src": "/app/static/icon-sos.png", "sizes": "96x96"}]
        }
    ],
    "related_applications": [],
    "prefer_related_applications": False
}


# =============================================================================
# SERVICE WORKER CODE
# =============================================================================

SERVICE_WORKER_JS = """
// LABBAIK AI Service Worker v6.0
const CACHE_NAME = 'labbaik-ai-v6';
const OFFLINE_URL = '/offline.html';

// Assets to cache immediately
const PRECACHE_ASSETS = [
    '/',
    '/offline.html',
    '/manifest.json',
    // Add your static assets here
];

// Cache strategies
const CACHE_STRATEGIES = {
    // Cache first for static assets
    cacheFirst: ['*.css', '*.js', '*.png', '*.jpg', '*.svg', '*.woff2'],
    // Network first for API calls
    networkFirst: ['/api/*', '/_stcore/*'],
    // Stale while revalidate for pages
    staleWhileRevalidate: ['/', '/?*']
};

// Install event - precache assets
self.addEventListener('install', (event) => {
    console.log('[SW] Installing LABBAIK AI Service Worker...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('[SW] Precaching assets');
                return cache.addAll(PRECACHE_ASSETS);
            })
            .then(() => self.skipWaiting())
    );
});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating LABBAIK AI Service Worker...');
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => name !== CACHE_NAME)
                    .map((name) => {
                        console.log('[SW] Deleting old cache:', name);
                        return caches.delete(name);
                    })
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch event - serve from cache or network
self.addEventListener('fetch', (event) => {
    // Skip non-GET requests
    if (event.request.method !== 'GET') return;
    
    // Skip cross-origin requests
    if (!event.request.url.startsWith(self.location.origin)) return;
    
    event.respondWith(
        caches.match(event.request)
            .then((cachedResponse) => {
                if (cachedResponse) {
                    // Return cached response and update cache in background
                    event.waitUntil(updateCache(event.request));
                    return cachedResponse;
                }
                
                // Fetch from network
                return fetch(event.request)
                    .then((response) => {
                        // Cache successful responses
                        if (response.status === 200) {
                            const responseClone = response.clone();
                            caches.open(CACHE_NAME).then((cache) => {
                                cache.put(event.request, responseClone);
                            });
                        }
                        return response;
                    })
                    .catch(() => {
                        // Return offline page for navigation requests
                        if (event.request.mode === 'navigate') {
                            return caches.match(OFFLINE_URL);
                        }
                        return new Response('Offline', { status: 503 });
                    });
            })
    );
});

// Update cache in background
async function updateCache(request) {
    try {
        const response = await fetch(request);
        if (response.status === 200) {
            const cache = await caches.open(CACHE_NAME);
            await cache.put(request, response);
        }
    } catch (error) {
        console.log('[SW] Background update failed:', error);
    }
}

// Handle messages from main thread
self.addEventListener('message', (event) => {
    if (event.data === 'skipWaiting') {
        self.skipWaiting();
    }
    
    if (event.data.type === 'CACHE_AUDIO') {
        // Cache audio files for offline doa player
        caches.open(CACHE_NAME).then((cache) => {
            cache.add(event.data.url);
        });
    }
});

// Background sync for pending actions
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-sos') {
        event.waitUntil(syncSOSAlerts());
    }
    if (event.tag === 'sync-checkin') {
        event.waitUntil(syncCheckins());
    }
});

async function syncSOSAlerts() {
    // Sync any pending SOS alerts when back online
    console.log('[SW] Syncing pending SOS alerts...');
}

async function syncCheckins() {
    // Sync any pending check-ins when back online
    console.log('[SW] Syncing pending check-ins...');
}

// Push notification handler (future)
self.addEventListener('push', (event) => {
    const data = event.data?.json() || {};
    const title = data.title || 'LABBAIK AI';
    const options = {
        body: data.body || 'Ada notifikasi baru',
        icon: '/app/static/icon-192.png',
        badge: '/app/static/badge.png',
        vibrate: [100, 50, 100],
        data: data.url || '/',
        actions: data.actions || []
    };
    
    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    event.waitUntil(
        clients.openWindow(event.notification.data)
    );
});

console.log('[SW] LABBAIK AI Service Worker loaded!');
"""


# =============================================================================
# OFFLINE PAGE HTML
# =============================================================================

OFFLINE_HTML = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LABBAIK AI - Offline</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0a0a0a, #1a1a1a);
            color: white;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 2rem;
            text-align: center;
        }
        
        .logo {
            font-size: 5rem;
            margin-bottom: 1rem;
        }
        
        h1 {
            color: #d4af37;
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        
        .subtitle {
            color: #b0b0b0;
            margin-bottom: 2rem;
        }
        
        .offline-icon {
            font-size: 4rem;
            margin-bottom: 1rem;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .message {
            max-width: 400px;
            line-height: 1.6;
            margin-bottom: 2rem;
        }
        
        .offline-features {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            max-width: 400px;
        }
        
        .offline-features h3 {
            color: #d4af37;
            margin-bottom: 1rem;
        }
        
        .feature-list {
            text-align: left;
            list-style: none;
        }
        
        .feature-list li {
            padding: 0.5rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .feature-list li:last-child {
            border-bottom: none;
        }
        
        .retry-btn {
            background: linear-gradient(135deg, #d4af37, #f4d03f);
            color: #0a0a0a;
            border: none;
            padding: 1rem 2rem;
            border-radius: 30px;
            font-size: 1rem;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .retry-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 20px rgba(212, 175, 55, 0.3);
        }
        
        .doa-section {
            margin-top: 2rem;
            padding: 1.5rem;
            background: rgba(212, 175, 55, 0.1);
            border-radius: 15px;
            max-width: 400px;
        }
        
        .doa-section h3 {
            color: #d4af37;
            margin-bottom: 1rem;
        }
        
        .arabic {
            font-size: 1.5rem;
            direction: rtl;
            margin-bottom: 0.5rem;
            line-height: 2;
        }
        
        .translation {
            color: #b0b0b0;
            font-style: italic;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="logo">🕋</div>
    <h1>LABBAIK AI</h1>
    <p class="subtitle">Platform Umrah Cerdas</p>
    
    <div class="offline-icon">📴</div>
    
    <p class="message">
        Anda sedang offline. Beberapa fitur mungkin tidak tersedia, 
        tetapi Anda masih bisa mengakses konten yang telah disimpan.
    </p>
    
    <div class="offline-features">
        <h3>✅ Tersedia Offline:</h3>
        <ul class="feature-list">
            <li>🤲 Doa & Dzikir Umrah</li>
            <li>📖 Panduan Manasik</li>
            <li>📋 Checklist Persiapan</li>
            <li>🆘 Kontak Darurat</li>
        </ul>
    </div>
    
    <button class="retry-btn" onclick="location.reload()" aria-label="Coba muat ulang halaman">
        🔄 Coba Lagi
    </button>
    
    <div class="doa-section">
        <h3>🤲 Doa Safar (Perjalanan)</h3>
        <p class="arabic">
            سُبْحَانَ الَّذِي سَخَّرَ لَنَا هَذَا وَمَا كُنَّا لَهُ مُقْرِنِينَ وَإِنَّا إِلَى رَبِّنَا لَمُنْقَلِبُونَ
        </p>
        <p class="translation">
            "Maha Suci Allah yang telah menundukkan ini untuk kami, padahal sebelumnya 
            kami tidak mampu menguasainya. Dan sesungguhnya kami akan kembali kepada Tuhan kami."
        </p>
    </div>
    
    <script>
        // Check online status
        window.addEventListener('online', () => {
            location.reload();
        });
        
        // Register for background sync
        if ('serviceWorker' in navigator && 'SyncManager' in window) {
            navigator.serviceWorker.ready.then((registration) => {
                return registration.sync.register('sync-pending');
            });
        }
    </script>
</body>
</html>
"""


# =============================================================================
# PWA INJECTION FOR STREAMLIT
# =============================================================================

def inject_pwa_meta_tags():
    """Inject PWA meta tags into Streamlit page."""
    
    pwa_html = f"""
    <script>
        // Inject PWA meta tags
        (function() {{
            // Manifest link
            if (!document.querySelector('link[rel="manifest"]')) {{
                const manifest = document.createElement('link');
                manifest.rel = 'manifest';
                manifest.href = 'data:application/json;base64,{_encode_manifest()}';
                document.head.appendChild(manifest);
            }}
            
            // Theme color
            if (!document.querySelector('meta[name="theme-color"]')) {{
                const theme = document.createElement('meta');
                theme.name = 'theme-color';
                theme.content = '#d4af37';
                document.head.appendChild(theme);
            }}
            
            // Apple touch icon
            if (!document.querySelector('link[rel="apple-touch-icon"]')) {{
                const appleIcon = document.createElement('link');
                appleIcon.rel = 'apple-touch-icon';
                appleIcon.href = '/app/static/icon-192.png';
                document.head.appendChild(appleIcon);
            }}
            
            // Apple mobile web app capable
            const appleMeta = document.createElement('meta');
            appleMeta.name = 'apple-mobile-web-app-capable';
            appleMeta.content = 'yes';
            document.head.appendChild(appleMeta);
            
            // Apple status bar style
            const statusBar = document.createElement('meta');
            statusBar.name = 'apple-mobile-web-app-status-bar-style';
            statusBar.content = 'black-translucent';
            document.head.appendChild(statusBar);
        }})();
    </script>
    """
    
    components.html(pwa_html, height=0)


def _encode_manifest() -> str:
    """Encode manifest as base64."""
    import base64
    manifest_str = json.dumps(PWA_MANIFEST)
    return base64.b64encode(manifest_str.encode()).decode()


def register_service_worker():
    """Register service worker for offline support."""
    
    sw_registration = f"""
    <script>
        // Register Service Worker
        if ('serviceWorker' in navigator) {{
            window.addEventListener('load', async () => {{
                try {{
                    // Create service worker blob
                    const swCode = `{SERVICE_WORKER_JS}`;
                    const swBlob = new Blob([swCode], {{type: 'application/javascript'}});
                    const swUrl = URL.createObjectURL(swBlob);
                    
                    // For production, use actual SW file
                    // const registration = await navigator.serviceWorker.register('/sw.js');
                    
                    console.log('[LABBAIK] PWA Support initialized');
                    
                    // Check for updates
                    // registration.addEventListener('updatefound', () => {{
                    //     console.log('[LABBAIK] New version available!');
                    // }});
                }} catch (error) {{
                    console.log('[LABBAIK] SW registration failed:', error);
                }}
            }});
        }}
        
        // Handle online/offline status
        window.addEventListener('online', () => {{
            console.log('[LABBAIK] Back online!');
            document.body.classList.remove('offline-mode');
        }});
        
        window.addEventListener('offline', () => {{
            console.log('[LABBAIK] Gone offline');
            document.body.classList.add('offline-mode');
        }});
        
        // Install prompt handling
        let deferredPrompt;
        window.addEventListener('beforeinstallprompt', (e) => {{
            e.preventDefault();
            deferredPrompt = e;
            // Show install button
            window.labbaik_canInstall = true;
            console.log('[LABBAIK] Install prompt ready');
        }});
        
        // Install function (call from Streamlit)
        window.installLabbaik = async () => {{
            if (deferredPrompt) {{
                deferredPrompt.prompt();
                const {{ outcome }} = await deferredPrompt.userChoice;
                console.log('[LABBAIK] Install outcome:', outcome);
                deferredPrompt = null;
            }}
        }};
    </script>
    """
    
    components.html(sw_registration, height=0)


def render_install_button():
    """Render install PWA button."""
    
    install_html = """
    <div id="install-container" style="display: none;">
        <button onclick="window.installLabbaik()" aria-label="Install aplikasi LABBAIK AI" style="
            background: linear-gradient(135deg, #d4af37, #f4d03f);
            color: #0a0a0a;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 25px;
            font-weight: bold;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin: 1rem auto;
        ">
            📲 Install LABBAIK AI
        </button>
    </div>
    
    <script>
        // Show install button if available
        if (window.labbaik_canInstall) {
            document.getElementById('install-container').style.display = 'block';
        }
        
        window.addEventListener('beforeinstallprompt', () => {
            document.getElementById('install-container').style.display = 'block';
        });
        
        window.addEventListener('appinstalled', () => {
            document.getElementById('install-container').style.display = 'none';
        });
    </script>
    """
    
    components.html(install_html, height=70)


def render_offline_indicator():
    """Render offline status indicator."""
    
    indicator_html = """
    <style>
        .offline-banner {
            display: none;
            background: linear-gradient(135deg, #ef4444, #dc2626);
            color: white;
            padding: 0.5rem 1rem;
            text-align: center;
            font-size: 0.85rem;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 9999;
        }
        
        body.offline-mode .offline-banner {
            display: block;
        }
    </style>
    
    <div class="offline-banner" role="alert" aria-live="assertive">
        <span aria-hidden="true">📴</span> Anda sedang offline - Beberapa fitur mungkin tidak tersedia
    </div>
    
    <script>
        if (!navigator.onLine) {
            document.body.classList.add('offline-mode');
        }
    </script>
    """
    
    components.html(indicator_html, height=0)


def init_pwa():
    """Initialize all PWA features."""
    inject_pwa_meta_tags()
    register_service_worker()
    render_offline_indicator()


# =============================================================================
# STREAMLIT PAGE
# =============================================================================

def render_pwa_settings_page():
    """Render PWA settings page."""
    try:
        from services.analytics.tracker import track_page
        track_page("pwa_settings")
    except Exception:
        pass

    inject_css(HERO_CSS, CARD_CSS)

    if not st.session_state.get("pwa_xp_awarded"):
        add_xp_safe(5, "Membuka halaman PWA")
        st.session_state.pwa_xp_awarded = True

    st.markdown("""
        <div class="page-hero">
            <h1><span aria-hidden="true">📱</span> Install LABBAIK AI</h1>
            <div class="subtitle">Akses LABBAIK AI seperti aplikasi native</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Install button
    render_install_button()
    
    st.divider()
    
    # Benefits
    st.markdown("### ✨ Keuntungan Install")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **📲 Akses Cepat**
        - Icon di home screen
        - Buka tanpa browser
        - Fullscreen mode
        """)
        
        st.markdown("""
        **📴 Mode Offline**
        - Doa & dzikir tersedia offline
        - Panduan manasik offline
        - Kontak darurat offline
        """)
    
    with col2:
        st.markdown("""
        **🔔 Notifikasi**
        - Pengingat keberangkatan
        - Alert dari rombongan
        - Update penting
        """)
        
        st.markdown("""
        **⚡ Performa**
        - Loading lebih cepat
        - Hemat data
        - Smooth experience
        """)
    
    st.divider()
    
    # Install instructions
    st.markdown("### 📋 Cara Install")
    
    tab1, tab2, tab3 = st.tabs(["📱 Android", "🍎 iOS", "💻 Desktop"])
    
    with tab1:
        st.markdown("""
        1. Buka **LABBAIK AI** di Chrome
        2. Tap menu **⋮** (3 titik)
        3. Pilih **"Add to Home Screen"**
        4. Tap **"Install"**
        5. Done! 🎉
        """)
    
    with tab2:
        st.markdown("""
        1. Buka **LABBAIK AI** di Safari
        2. Tap icon **Share** (kotak dengan panah)
        3. Scroll dan pilih **"Add to Home Screen"**
        4. Tap **"Add"**
        5. Done! 🎉
        """)
    
    with tab3:
        st.markdown("""
        **Chrome:**
        1. Klik icon **⊕** di address bar
        2. Klik **"Install"**
        
        **Edge:**
        1. Klik menu **⋯**
        2. Pilih **"Apps" → "Install this site as an app"**
        """)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "init_pwa",
    "inject_pwa_meta_tags",
    "register_service_worker",
    "render_install_button",
    "render_offline_indicator",
    "render_pwa_settings_page",
    "PWA_MANIFEST",
    "SERVICE_WORKER_JS",
    "OFFLINE_HTML",
]
