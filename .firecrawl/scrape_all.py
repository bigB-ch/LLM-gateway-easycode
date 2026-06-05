"""Scrape all pricing data from all pages and all providers."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright
import json, time, re

def scrape():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            locale='zh-CN',
        )
        page = context.new_page()

        all_text = ""

        # Go directly to model square (pricing page)
        print("=== Loading model square ===")
        page.goto('https://ai.huosanyun.com/pricing', wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(5000)

        # Get page 1
        text1 = page.locator('body').first.inner_text()
        all_text += text1 + "\n\n"
        with open('.firecrawl/page1_text.txt', 'w', encoding='utf-8') as f:
            f.write(text1)
        print(f"Page 1: {len(text1)} chars")

        # Click page 2
        try:
            page2_btn = page.locator('text="2"').last
            if page2_btn.is_visible():
                page2_btn.click()
                page.wait_for_timeout(3000)
                text2 = page.locator('body').first.inner_text()
                all_text += text2 + "\n\n"
                with open('.firecrawl/page2_text.txt', 'w', encoding='utf-8') as f:
                    f.write(text2)
                print(f"Page 2: {len(text2)} chars")

                # Check for page 3
                try:
                    page3_btn = page.locator('text="3"').last
                    if page3_btn.is_visible():
                        page3_btn.click()
                        page.wait_for_timeout(3000)
                        text3 = page.locator('body').first.inner_text()
                        all_text += text3 + "\n\n"
                        with open('.firecrawl/page3_text.txt', 'w', encoding='utf-8') as f:
                            f.write(text3)
                        print(f"Page 3: {len(text3)} chars")
                except:
                    print("No page 3")
        except Exception as e:
            print(f"No page 2: {e}")

        # Save complete text
        with open('.firecrawl/all_pricing_text.txt', 'w', encoding='utf-8') as f:
            f.write(all_text)
        print(f"\nTotal text: {len(all_text)} chars")

        # Screenshot
        page.screenshot(path='.firecrawl/pricing_final.png', full_page=True)

        # Try to expand to show more per page
        # Look for "20 / page" selector and try to change it
        try:
            page_size = page.locator('text="20"').first
            if page_size.is_visible():
                print(f"Page size element: {page_size.inner_text()}")
        except:
            pass

        browser.close()

if __name__ == '__main__':
    scrape()
