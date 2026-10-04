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
    time.sleep(3)

    print("Looking for Turnstile iframe/checkbox...")
    # Find Cloudflare frame
    for attempt in range(15):
        cf_frame = None
        for f in page.frames:
            if "challenges.cloudflare.com" in f.url:
                cf_frame = f
                break
        
        if cf_frame:
            print(f"Found CF frame on attempt {attempt}: {cf_frame.url[:60]}")
            try:
                # Look for checkbox or clickable element in frame
                box = cf_frame.locator("input[type='checkbox']")
                if box.count() > 0 and box.is_visible():
                    print("Found checkbox! Clicking...")
                    box.click(force=True)
                    time.sleep(2)
                else:
                    label = cf_frame.locator("label, .ctp-checkbox-label, .mark, span")
                    if label.count() > 0:
                        print("Clicking label inside CF frame...")
                        label.first.click(force=True)
                        time.sleep(2)
            except Exception as e:
                print("Click in frame failed:", e)
                # Try clicking iframe by coordinates
                iframe_el = page.query_selector("iframe[src*='challenges.cloudflare.com']")
                if iframe_el:
                    bb = iframe_el.bounding_box()
                    if bb and bb["width"] > 0:
                        print(f"Clicking iframe coordinates: {bb}")
                        page.mouse.click(bb["x"] + 30, bb["y"] + bb["height"] / 2)
                        time.sleep(2)

        token = page.evaluate("async () => { try { return await window.FreegenSession.get(); } catch(e) { return null; } }")
        if token:
            print(f"SUCCESS! Got FreegenSession token: {token[:40]}...")
            break
        time.sleep(1)

    screenshot_path = r"E:\Open-Generative-AI-main\AutoImageFlow\turnstile_after_click.png"
    page.screenshot(path=screenshot_path)
    print(f"Saved screenshot to {screenshot_path}")

    if token:
        # Now try generating!
        prompt_sel = "#prompt"
        gen_btn = "#generateBtn"
        page.fill(prompt_sel, "A magical glowing crystal tree, fantasy art")
        print("Clicking Generate with valid token...")
        page.click(gen_btn, force=True)
        
        for s in range(30):
            time.sleep(1)
            btn_text = page.inner_text(gen_btn)
            img_html = page.inner_html("#imageContainer")
            print(f"[{s}s] btnText: {btn_text}, imgHTML len: {len(img_html)}")
            if len(img_html) > 50 and "<img" in img_html:
                print("IMAGE GENERATED SUCCESSFULLY!")
                break
                
        page.screenshot(path=r"E:\Open-Generative-AI-main\AutoImageFlow\generation_success.png")

    browser.close()
