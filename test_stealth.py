from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import time

with sync_playwright() as p:
    b = p.chromium.launch_persistent_context(
        user_data_dir=r"E:\Temp\playwright-artifacts",
        headless=False,
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = b.pages[0] if b.pages else b.new_page()
    Stealth().apply_stealth_sync(page)
    
    print("Navigating to https://freegen.app...")
    page.goto("https://freegen.app", wait_until="domcontentloaded")
    time.sleep(3)
    
    page.fill("#prompt", "A golden majestic lion resting on a cliff at sunset")
    print("Clicking Generate with stealth enabled...")
    page.click("#generateBtn", force=True)
    
    for s in range(35):
        time.sleep(1)
        btn_text = page.inner_text("#generateBtn")
        imgs = page.query_selector_all("#imageContainer img")
        print(f"[{s}s] btnText: '{btn_text}', imgs count: {len(imgs)}")
        if imgs:
            for img in imgs:
                src = img.get_attribute("src")
                print("SUCCESSFUL IMAGE GENERATED:", src[:80] if src else "")
            break
            
    page.screenshot(path=r"E:\Open-Generative-AI-main\AutoImageFlow\stealth_test_result.png")
    b.close()
