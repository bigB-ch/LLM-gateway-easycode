"""Login to ai.huosanyun.com and extract all pricing data."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright
import json, time, re

EMAIL = "BigB"
PASSWORD = "zhangzzb0752"

def scrape():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            locale='zh-CN',
        )
        page = context.new_page()

        # Step 1: Go to login page
        print("Navigating to login...")
        page.goto('https://ai.huosanyun.com/login', wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(3000)
        print(f"Current URL: {page.url}")

        # Step 2: Fill login form
        try:
            email_selectors = ['input[type="email"]', 'input[type="text"]', 'input[name="email"]', 'input[name="username"]']
            password_selectors = ['input[type="password"]']

            email_field = None
            for sel in email_selectors:
                el = page.locator(sel).first
                if el.is_visible():
                    email_field = el
                    print(f"Found email field: {sel}")
                    break

            password_field = None
            for sel in password_selectors:
                el = page.locator(sel).first
                if el.is_visible():
                    password_field = el
                    print(f"Found password field: {sel}")
                    break

            if email_field and password_field:
                email_field.fill(EMAIL)
                password_field.fill(PASSWORD)
                print("Filled credentials")

                # Click login button
                button_selectors = ['button[type="submit"]', 'button:has-text("login")', 'button:has-text("Login")', 'button:has-text("deng lu")']
                clicked = False
                for sel in button_selectors:
                    try:
                        btn = page.locator(sel).first
                        if btn.is_visible():
                            btn.click()
                            print(f"Clicked: {sel}")
                            clicked = True
                            break
                    except:
                        pass

                # Try pressing Enter as fallback
                if not clicked:
                    password_field.press('Enter')
                    print("Pressed Enter")

                page.wait_for_timeout(5000)
                print(f"After login URL: {page.url}")
            else:
                print("Could not find login fields")
                page.screenshot(path='.firecrawl/login_debug.png', full_page=True)
                body = page.locator('body').first
                if body:
                    with open('.firecrawl/login_page.txt', 'w', encoding='utf-8') as f:
                        f.write(body.inner_text())
                print("Saved debug files")

        except Exception as e:
            print(f"Login error: {e}")

        # Step 3: Navigate to pricing page
        print("\nNavigating to pricing...")
        page.goto('https://ai.huosanyun.com/pricing', wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(8000)

        # Save everything
        text = page.locator('body').first.inner_text()
        with open('.firecrawl/pricing_text.txt', 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Saved pricing text ({len(text)} chars)")

        page.screenshot(path='.firecrawl/pricing_screenshot.png', full_page=True)
        print("Saved screenshot")

        html = page.content()
        with open('.firecrawl/pricing_full.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"Saved HTML ({len(html)} chars)")

        # Find tables
        tables = page.locator('table').all()
        print(f"\nFound {len(tables)} HTML tables")

        # Extract text for key terms
        for term in ['model', 'price', 'token', 'input', 'output']:
            count = text.lower().count(term)
            print(f"  '{term}': {count}")

        # Print the text content for review
        print("\n=== TEXT CONTENT ===")
        print(text[:10000])

        browser.close()

if __name__ == '__main__':
    scrape()
