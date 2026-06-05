"""Login with Playwright v2 - click correct buttons."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright
import json, time

EMAIL = "BigB"
PASSWORD = "zhangzzb0752"

def login_and_scrape():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(locale='zh-CN')
        page = context.new_page()

        # Capture API responses
        api_data = []
        def handle_response(response):
            url = response.url
            if '/api/' in url and response.status == 200:
                try:
                    ct = response.headers.get('content-type', '')
                    if 'json' in ct:
                        data = response.json()
                        print(f"API: {url}")
                        api_data.append({'url': url, 'data': data})
                except:
                    pass
        page.on('response', handle_response)

        # Go to login page
        print("Navigating to login...")
        page.goto('https://ai.huosanyun.com/login', wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(3000)

        # Check if it's a two-step login (email first, then password)
        # Fill email first
        inputs = page.locator('input').all()
        print(f"Found {len(inputs)} inputs")
        for i, inp in enumerate(inputs):
            try:
                ph = inp.get_attribute('placeholder') or ''
                tp = inp.get_attribute('type') or ''
                print(f"  Input {i}: type={tp}, placeholder={ph}")
            except:
                pass

        # Check buttons
        btns = page.locator('button').all()
        for i, btn in enumerate(btns):
            try:
                txt = btn.inner_text()
                print(f"  Button {i}: '{txt}'")
            except:
                pass

        # Try filling email first
        email_input = page.locator('input[type="text"]').first
        if email_input.is_visible():
            email_input.fill(EMAIL)
            print("Filled email")

        # Click "继续" (Continue) button if present (two-step flow)
        continue_btn = page.locator('button:has-text("继续")')
        if continue_btn.is_visible():
            continue_btn.click()
            print("Clicked Continue")
            page.wait_for_timeout(3000)

            # Now fill password
            password_input = page.locator('input[type="password"]').first
            if password_input.is_visible():
                password_input.fill(PASSWORD)
                print("Filled password")

        # Click login button
        login_btn = page.locator('button:has-text("登录")')
        if login_btn.is_visible():
            login_btn.click()
            print("Clicked Login")
        else:
            # Try Enter key
            page.keyboard.press('Enter')
            print("Pressed Enter")

        page.wait_for_timeout(5000)
        print(f"After login URL: {page.url}")

        # Save screenshot to check
        page.screenshot(path='.firecrawl/after_login.png')

        if 'login' not in page.url:
            print("SUCCESS - logged in!")
            # Go to pricing
            page.goto('https://ai.huosanyun.com/pricing', wait_until='networkidle', timeout=60000)
            page.wait_for_timeout(5000)
        else:
            print("Login seems to have failed")
            # Check for error messages
            body_text = page.locator('body').first.inner_text()
            print(f"Page text: {body_text[:500]}")

        # Print all API data
        print(f"\n=== {len(api_data)} API responses ===")
        for resp in api_data:
            url = resp['url']
            if 'status' not in url:
                data_str = json.dumps(resp['data'], ensure_ascii=False)
                if len(data_str) > 8000:
                    data_str = data_str[:8000] + "..."
                print(f"\n--- {url} ---")
                print(data_str)

        browser.close()

if __name__ == '__main__':
    login_and_scrape()
