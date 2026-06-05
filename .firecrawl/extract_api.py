"""Extract all pricing data from the API."""
import urllib.request, ssl, json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Fetch pricing data
req = urllib.request.Request(
    'https://ai.huosanyun.com/api/pricing',
    headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://ai.huosanyun.com/pricing'}
)
resp = urllib.request.urlopen(req, context=ctx, timeout=30)
data = json.loads(resp.read().decode('utf-8'))

# From /api/status: price=1, quota_per_unit=500000
# Formula: display_price_per_1M = ratio * base_price / (quota_per_unit/1000000)
#   = ratio * 1 / 0.5 = ratio * 2
BASE_PRICE = 1
QUOTA_PER_UNIT = 500000
PRICE_MULTIPLIER = BASE_PRICE / (QUOTA_PER_UNIT / 1000000)

models = data['data']
print(f"Total models: {len(models)}")
print("=" * 80)

all_models = []
for m in models:
    name = m['model_name']
    vendor_id = m['vendor_id']
    quota_type = m['quota_type']  # 0=per-token, 1=per-use
    model_ratio = m.get('model_ratio', 0)
    completion_ratio = m.get('completion_ratio', 0)
    cache_ratio = m.get('cache_ratio', 0)
    model_price = m.get('model_price', 0)
    tags = m.get('tags', '')
    desc = m.get('description', '')
    icon = m.get('icon', '')

    model_entry = {
        'name': name,
        'vendor_id': vendor_id,
        'icon': icon,
        'quota_type': 'per-token' if quota_type == 0 else 'per-use',
        'description': desc,
        'tags': tags,
    }

    if quota_type == 1:
        # Per-use pricing
        model_entry['price_per_use'] = model_price
        print(f"{name} | vendor={vendor_id} | CNY{model_price}/use | {tags}")
    else:
        input_price = round(model_ratio * PRICE_MULTIPLIER, 4)
        output_price = round(model_ratio * completion_ratio * PRICE_MULTIPLIER, 4)
        cache_read_price = round(model_ratio * cache_ratio * PRICE_MULTIPLIER, 4) if cache_ratio else None
        model_entry['input_price_1M'] = input_price
        model_entry['output_price_1M'] = output_price
        model_entry['cache_read_price_1M'] = cache_read_price
        model_entry['model_ratio'] = model_ratio
        model_entry['completion_ratio'] = completion_ratio
        model_entry['cache_ratio'] = cache_ratio

        cache_str = f" | cache: {cache_read_price}" if cache_read_price else ""
        print(f"{name} | vendor={vendor_id} | input: CNY{input_price} | output: CNY{output_price}{cache_str} | {tags}")

    all_models.append(model_entry)

# Save structured data
output = {
    'source': 'https://ai.huosanyun.com/api/pricing',
    'base_price': BASE_PRICE,
    'quota_per_unit': QUOTA_PER_UNIT,
    'price_multiplier': PRICE_MULTIPLIER,
    'total_models': len(models),
    'models': all_models,
}
with open('.firecrawl/all_models.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\nSaved to all_models.json")

# Also print vendor IDs
vendor_ids = sorted(set(m['vendor_id'] for m in models))
print(f"\nVendor IDs ({len(vendor_ids)}): {vendor_ids}")
