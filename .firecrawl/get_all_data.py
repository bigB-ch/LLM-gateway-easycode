"""Get vendor names and try login for more models."""
import urllib.request, ssl, json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Get vendor info from the JS bundle
req = urllib.request.Request(
    'https://ai.huosanyun.com/assets/index-SGpNKur2.js',
    headers={'User-Agent': 'Mozilla/5.0'}
)
resp = urllib.request.urlopen(req, context=ctx, timeout=30)
js = resp.read().decode('utf-8')

# Search for vendor name/id mappings
import re

# Pattern: {value:N,color:"...",label:"VendorName"}
vendor_matches = re.findall(r'\{value:(\d+),color:"[^"]*",label:"([^"]*)"\}', js)
print("=== Vendor mappings from JS ===")
vendors = {}
for vid, name in sorted(set(vendor_matches), key=lambda x: int(x[0])):
    vendors[int(vid)] = name
    print(f"  {vid}: {name}")

# Now map vendor_ids from pricing data to names
print("\n=== Model pricing with vendor names ===")
req2 = urllib.request.Request(
    'https://ai.huosanyun.com/api/pricing',
    headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://ai.huosanyun.com/pricing'}
)
resp2 = urllib.request.urlopen(req2, context=ctx, timeout=30)
pricing = json.loads(resp2.read().decode('utf-8'))

PRICE_MULT = 2  # 1 / (500000/1000000) = 2

for m in pricing['data']:
    name = m['model_name']
    vid = m['vendor_id']
    vendor_name = vendors.get(vid, f"Unknown-{vid}")
    qt = m.get('quota_type', 0)
    mr = m.get('model_ratio', 0)
    cr = m.get('completion_ratio', 0)
    car = m.get('cache_ratio', 0)
    mp = m.get('model_price', 0)
    tags = m.get('tags', '')

    if qt == 1:
        print(f"{vendor_name} | {name} | CNY{mp}/use | {tags}")
    else:
        inp = round(mr * PRICE_MULT, 4)
        out = round(mr * cr * PRICE_MULT, 4)
        cache = f" | cache: CNY{round(mr * car * PRICE_MULT, 4)}" if car else ""
        print(f"{vendor_name} | {name} | in: CNY{inp} | out: CNY{out}{cache} | {tags}")

# Also check models/search with login
print("\n=== Trying login to get more models ===")
import urllib.parse
login_data = urllib.parse.urlencode({
    'username': 'BigB',
    'password': 'zhangzzb0752'
}).encode('utf-8')

try:
    login_req = urllib.request.Request(
        'https://ai.huosanyun.com/api/user/login',
        data=login_data,
        headers={'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/x-www-form-urlencoded'}
    )
    login_resp = urllib.request.urlopen(login_req, context=ctx, timeout=30)
    login_result = json.loads(login_resp.read().decode('utf-8'))
    print(f"Login result: {json.dumps(login_result, ensure_ascii=False)[:500]}")

    if login_result.get('success'):
        token = login_result.get('data', {}).get('token', '')
        if token:
            print(f"Got token: {token[:20]}...")
            # Try models/search
            search_req = urllib.request.Request(
                'https://ai.huosanyun.com/api/models/search?page=0&size=200',
                headers={'User-Agent': 'Mozilla/5.0', 'Authorization': f'Bearer {token}'}
            )
            search_resp = urllib.request.urlopen(search_req, context=ctx, timeout=30)
            search_data = json.loads(search_resp.read().decode('utf-8'))
            count = len(search_data.get('data', []))
            print(f"Models from search API: {count}")
            for m in search_data.get('data', [])[:10]:
                print(f"  {m.get('model_name', '?')} - {m.get('vendor_name', '?')}")
except Exception as e:
    print(f"Login error: {e}")
