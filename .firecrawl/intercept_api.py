"""Intercept API calls to get model pricing data."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    from playwright.sync_api import sync_playwright
except:
    # Skip if playwright not available
    pass
import json, time

def intercept():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(locale='zh-CN')
        page = context.new_page()

        # Store all API responses
        api_responses = []

        def handle_response(response):
            url = response.url
            if '/api/' in url and response.status == 200:
                try:
                    ct = response.headers.get('content-type', '')
                    if 'json' in ct:
                        data = response.json()
                        api_responses.append({'url': url, 'data': data})
                        print(f"Captured: {url}")
                except:
                    pass

        page.on('response', handle_response)

        # Go to pricing page
        print("Loading pricing page...")
        page.goto('https://ai.huosanyun.com/pricing', wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(5000)

        # Print what we captured
        print(f"\n=== Captured {len(api_responses)} API responses ===")
        for i, resp in enumerate(api_responses):
            url = resp['url']
            print(f"\n--- Response {i}: {url} ---")
            data = resp['data']
            # Pretty print (limit size)
            s = json.dumps(data, ensure_ascii=False, indent=2)
            if len(s) > 5000:
                s = s[:5000] + "...(truncated)"
            print(s)

        # Also output to JSON file
        with open('.firecrawl/api_responses.json', 'w', encoding='utf-8') as f:
            json.dump(api_responses, f, ensure_ascii=False, indent=2)

        browser.close()

if __name__ == '__main__':
    intercept()
