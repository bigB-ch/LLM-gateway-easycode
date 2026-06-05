"""Login with Playwright and capture all API responses."""
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

        # Capture ALL API responses
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

        # Go to login page
        print("Going to login page...")
        page.goto('https://ai.huosanyun.com/login', wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(3000)

        # Fill credentials
        email_input = page.locator('input[type="text"]').first
        password_input = page.locator('input[type="password"]').first
        email_input.fill(EMAIL)
        password_input.fill(PASSWORD)
        print("Filled credentials")

        # Click login - try different approaches
        # First try to find the login button by text
        try:
            # Semi-UI button - look for button with text
            login_btn = page.locator('button:has-text("deng lu")').first
            if login_btn.is_visible():
                login_btn.click()
                print("Clicked login button")
        except:
            pass

        if not login_btn or not login_btn.is_visible():
            # Try any button in the form
            btns = page.locator('button').all()
            print(f"Found {len(btns)} buttons")
            for i, btn in enumerate(btns):
                try:
                    txt = btn.inner_text()
                    print(f"  Button {i}: '{txt}'")
                    if any(kw in txt for kw in ['deng', 'login', 'sign']):
                        btn.click()
                        print(f"Clicked button {i}")
                        break
                except:
                    pass

        page.wait_for_timeout(5000)
        print(f"After login URL: {page.url}")

        # If login succeeded, go to pricing
        if 'login' not in page.url:
            print("Login successful!")
            page.goto('https://ai.huosanyun.com/pricing', wait_until='networkidle', timeout=60000)
            page.wait_for_timeout(5000)

            # Check models count
            text = page.locator('body').first.inner_text()
            model_count = text.count('输入价格') + text.count('补全价格') + text.count('模型价格')
            print(f"Pricing indicators found: {model_count}")

        # Print all captured API data
        print(f"\n=== Captured {len(api_data)} API responses ===")
        for resp in api_data:
            url = resp['url']
            print(f"\n{url}")
            data_str = json.dumps(resp['data'], ensure_ascii=False)
            if len(data_str) > 3000:
                data_str = data_str[:3000] + "..."
            print(data_str)

        browser.close()

if __name__ == '__main__':
    login_and_scrape()
