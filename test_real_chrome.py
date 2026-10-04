from playwright.sync_api import sync_playwright
import time

print("Launching REAL Google Chrome via Playwright...")
with sync_playwright() as p:
    b = p.chromium.launch_persistent_context(
        user_data_dir=r"E:\Temp\playwright-chrome-real",
        channel="chrome",
        headless=False,
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = b.pages[0] if b.pages else b.new_page()
    page.goto("https://freegen.app", wait_until="domcontentloaded")
    time.sleep(3)
    
    page.fill("#prompt", "A majestic glowing crystal stag in an enchanted forest, 8k")
    print("Clicking Generate in real Chrome...")
    page.click("#generateBtn", force=True)
    
    for s in range(40):
        time.sleep(1)
        btn_text = page.inner_text("#generateBtn")
        imgs = page.query_selector_all("#imageContainer img")
        print(f"[{s}s] btnText: '{btn_text}', imgs: {len(imgs)}")
        if imgs:
            for img in imgs:
                src = img.get_attribute("src")
                print("FOUND IMAGE IN REAL CHROME! src:", src[:80] if src else "")
            break
            
    page.screenshot(path=r"E:\Open-Generative-AI-main\AutoImageFlow\real_chrome_result.png")
    b.close()
