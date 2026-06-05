"""Render the pricing page using Playwright and extract model pricing data."""
from playwright.sync_api import sync_playwright
import json, time, re

def extract_pricing():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            locale='zh-CN',
        )
        page = context.new_page()

        print("Loading pricing page...")
        page.goto('https://ai.huosanyun.com/pricing', wait_until='networkidle', timeout=60000)

        # Wait for the table to render
        page.wait_for_timeout(5000)

        # Save full page HTML for analysis
        html = page.content()
        with open('.firecrawl/pricing_full.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"Saved HTML ({len(html)} chars)")

        # Take screenshot
        page.screenshot(path='.firecrawl/pricing_screenshot.png', full_page=True)
        print("Saved screenshot")

        # Try to extract text content
        text = page.inner_text('body')
        with open('.firecrawl/pricing_text.txt', 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Saved text content ({len(text)} chars)")

        # Try to find tables
        tables = page.locator('table').all()
        print(f"Found {len(tables)} tables")
        for i, table in enumerate(tables):
            try:
                table_text = table.inner_text()
                print(f"\nTable {i}: {table_text[:500]}")
            except Exception as e:
                print(f"Table {i}: error - {e}")

        # Try to find div/tr with pricing data
        rows = page.locator('[class*="row"], [class*="item"], [class*="model"], tr, [role="row"]').all()
        print(f"\nFound {len(rows)} potential rows")

        # Try to detect if we're on the pricing page
        page_title = page.title()
        print(f"\nPage title: {page_title}")

        # Check current URL
        print(f"Current URL: {page.url}")

        browser.close()

if __name__ == '__main__':
    extract_pricing()
