import urllib.request
import ssl
import re
import json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request(
    'https://ai.huosanyun.com/assets/index-SGpNKur2.js',
    headers={'User-Agent': 'Mozilla/5.0'}
)
resp = urllib.request.urlopen(req, context=ctx, timeout=30)
js = resp.read().decode('utf-8')

# Look for API endpoints - search for URL-like strings
patterns = [
    r"https?://[a-zA-Z0-9._/]+/[a-zA-Z]+/[a-zA-Z]+",
    r'/[a-z]+/[a-z]+/[a-z]+',
    r'"([a-zA-Z]+://[^"]*api[^"]*)"',
    r'([a-zA-Z]+://[^"]*)"',
]
for pattern in patterns:
    matches = list(set(re.findall(pattern, js, re.IGNORECASE)))
    matches = [m for m in matches if 'ahref' not in m and 'href' not in m]
    if matches:
        print(f'Pattern: {pattern}')
        for m in sorted(matches)[:30]:
            print(f'  {m}')
        print()

# Search for model data in JS - look for embedded JSON with pricing
# Look for large JSON arrays/objects
json_like = re.findall(r'\{[^}]{100,1000}\}', js)
print(f'\nFound {len(json_like)} JSON-like objects > 100 chars')
for j in json_like[:20]:
    if 'model' in j.lower() or 'price' in j.lower() or 'token' in j.lower():
        print(j[:500])
        print('---')
