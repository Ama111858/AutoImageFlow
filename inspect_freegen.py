import urllib.request
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request('https://freegen.app', headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
html = urllib.request.urlopen(req, context=ctx, timeout=10).read().decode('utf-8', errors='ignore')

scripts = re.findall(r'<script[^>]*src=["\']([^"\']+)["\']', html)
print('Script src files:', scripts)

inline = re.findall(r'<script(?![^>]*src)[^>]*>(.*?)</script>', html, re.DOTALL)
print(f'Inline script blocks: {len(inline)}')

for i, s in enumerate(inline):
    if 'generate' in s or 'prompt' in s or 'skipAd' in s:
        print(f"\n--- INLINE SCRIPT {i} ---")
        lines = [l for l in s.splitlines() if l.strip()]
        for l in lines[:60]:
            print(l[:120])
