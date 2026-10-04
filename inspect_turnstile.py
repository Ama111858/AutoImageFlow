from playwright.sync_api import sync_playwright
import time
import os

artifacts_dir = r"E:\Temp\playwright-artifacts"

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir=artifacts_dir,
        headless=False,
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = browser.pages[0] if browser.pages else browser.new_page()
    page.goto("https://freegen.app", wait_until="domcontentloaded")
    time.sleep(5)
    
    # Check turnstile widget
    widget = page.query_selector("#turnstileWidget")
    print("Widget element:", widget)
    if widget:
        print("Widget innerHTML:", page.inner_html("#turnstileWidget"))
        print("Widget bounding box:", widget.bounding_box())
        
    frames = page.frames
    print(f"Total frames on page: {len(frames)}")
    for f in frames:
        if "cloudflare" in f.url or "turnstile" in f.url or "challenge" in f.url:
            print("Found CF frame:", f.url)
            # Try to see if there's a checkbox inside this frame
            try:
                checkbox = f.query_selector("input[type='checkbox']")
                print("  Checkbox:", checkbox)
                content = f.content()
                print("  Frame content snippet:", content[:200])
            except Exception as e:
                print("  Error querying frame:", e)
                
    browser.close()
