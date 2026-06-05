"""Login with Playwright v3 - fill both fields, click login."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright
import json, time, re

EMAIL = "BigB"
PASSWORD = "zhangzzb0752"
PRICE_MULT = 2  # base/ (quota_per_unit/1M) = 1 / 0.5 = 2

def login_and_scrape():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(locale='zh-CN')
        page = context.new_page()

        api_data = []
        def handle_response(response):
            url = response.url
            if '/api/' in url and response.status == 200:
                try:
                    ct = response.headers.get('content-type', '')
                    if 'json' in ct:
                        data = response.json()
                        api_data.append({'url': url, 'data': data})
                except:
                    pass
        page.on('response', handle_response)

        # Step 1: Go to login and fill both fields
        print("Logging in...")
        page.goto('https://ai.huosanyun.com/login', wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(3000)

        # Fill both email and password
        email_input = page.locator('input[type="text"]').first
        password_input = page.locator('input[type="password"]').first
        email_input.fill(EMAIL)
        password_input.fill(PASSWORD)
        print("Filled both fields")

        # Click login button
        login_btn = page.locator('button:has-text("登录")')
        if login_btn.is_visible():
            # Check if enabled
            disabled = login_btn.get_attribute('disabled')
            print(f"Login button disabled: {disabled}")
            if not disabled:
                login_btn.click()
                print("Clicked Login")
            else:
                print("Login button disabled, trying Enter")
                password_input.press('Enter')
        else:
            page.keyboard.press('Enter')
            print("Pressed Enter")

        page.wait_for_timeout(5000)
        print(f"URL after login: {page.url}")

        # Check for error
        text = page.locator('body').first.inner_text()
        if '用户名或密码' in text or '错误' in text or '失败' in text:
            print(f"ERROR: {text[:500]}")
        elif 'login' not in page.url:
            print("LOGIN SUCCESS!")

        # Step 2: Go to pricing regardless
        print("\nNavigating to pricing...")
        page.goto('https://ai.huosanyun.com/pricing', wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(5000)

        # Step 3: Go to console page to get more models
        print("\nNavigating to console (logged in area)...")
        page.goto('https://ai.huosanyun.com/', wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(5000)
        print(f"Home URL: {page.url}")

        # Print all API data except status
        print(f"\n=== {len(api_data)} API responses captured ===")
        for resp in api_data:
            url = resp['url']
            if 'status' not in url:
                data = resp['data']
                data_str = json.dumps(data, ensure_ascii=False)
                if len(data_str) > 10000:
                    data_str = data_str[:10000] + "..."
                print(f"\n--- {url} ---")
                print(data_str)

        # Also save to file
        with open('.firecrawl/all_api_data.json', 'w', encoding='utf-8') as f:
            json.dump(api_data, f, ensure_ascii=False, indent=2)
        print("\nSaved all API data")

        browser.close()

if __name__ == '__main__':
    login_and_scrape()
