from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    b = p.chromium.launch_persistent_context(r"E:\Temp\playwright-artifacts", headless=False)
    page = b.pages[0] if b.pages else b.new_page()
    page.goto("https://freegen.app", wait_until="domcontentloaded")
    time.sleep(3)
    page.click("#generateBtn", force=True)
    time.sleep(3)
    
    for f in page.frames:
        if "challenges.cloudflare.com" in f.url:
            for cf in f.child_frames:
                if "srcdoc" in cf.url:
                    print("Found srcdoc frame!")
                    try:
                        print("Body snippet:", cf.inner_html("body")[:300])
                        cb = cf.locator("input[type='checkbox']")
                        print("Found checkbox count:", cb.count())
                        if cb.count() > 0:
                            print("Clicking checkbox in srcdoc frame!")
                            cb.first.click()
                            time.sleep(4)
                    except Exception as e:
                        print("Err:", e)
                        
    # Check if turnstile token is delivered
    token = page.evaluate("async () => { try { return await window.FreegenSession.get(); } catch(e) { return null; } }")
    print("Token after click:", token[:50] if token else "None")
    
    page.screenshot(path=r"E:\Open-Generative-AI-main\AutoImageFlow\after_srcdoc_click.png")
    b.close()
