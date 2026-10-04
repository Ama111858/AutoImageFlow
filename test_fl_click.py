from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    b = p.chromium.launch_persistent_context(r"E:\Temp\playwright-artifacts", headless=False)
    page = b.pages[0] if b.pages else b.new_page()
    page.goto("https://freegen.app", wait_until="domcontentloaded")
    time.sleep(3)
    page.click("#generateBtn", force=True)
    time.sleep(3)
    
    # Try clicking using frame_locator
    try:
        cf = page.frame_locator("iframe[src*='challenges.cloudflare.com']")
        print("CF frame locator created.")
        # Click the body or checkbox of the turnstile
        cf.locator("body").click()
        print("Clicked cf locator body!")
    except Exception as e:
        print("Error frame_locator:", e)
        
    time.sleep(5)
    page.screenshot(path=r"E:\Open-Generative-AI-main\AutoImageFlow\cf_framelocator_click.png")
    b.close()
