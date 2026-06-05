"""Analyze JS bundles for pricing data."""
import urllib.request, ssl, re, json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, context=ctx, timeout=30)
    return resp.read().decode('utf-8')

# Check if pricing page needs login
req = urllib.request.Request(
    'https://ai.huosanyun.com/pricing',
    headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
)
resp = urllib.request.urlopen(req, context=ctx, timeout=30)
print(f"Status: {resp.status}, Final URL: {resp.url}")

# Check JS for embedded pricing data
js_files = [
    'index-SGpNKur2.js',
    'react-components-BnylIsR_.js',
    'tools-DAe9LAam.js',
]
for js_file in js_files:
    try:
        js = fetch(f'https://ai.huosanyun.com/assets/{js_file}')
        print(f"\n--- {js_file}: {len(js)} chars ---")

        # Search for model names followed by pricing
        # Look for patterns like "gpt-4" with prices nearby
        matches = re.findall(r'(["](gpt|claude|gemini|deepseek|qwen|llama|mistral|yi|moonshot|kimi)[^"]*["])', js, re.IGNORECASE)
        for m in matches[:20]:
            idx = js.find(m[0])
            context = js[max(0,idx-100):idx+len(m[0])+200]
            print(f"  Found: {m[0][:50]} at {idx}, context: {context[:150]}...")

    except Exception as e:
        print(f"Error fetching {js_file}: {e}")
