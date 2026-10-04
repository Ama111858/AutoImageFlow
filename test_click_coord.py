from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    b = p.chromium.launch_persistent_context(
        user_data_dir=r"E:\Temp\playwright-artifacts",
        headless=False,
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = b.pages[0] if b.pages else b.new_page()
    page.goto("https://freegen.app", wait_until="domcontentloaded")
    time.sleep(4)

    # Find the iframe on page
    iframe_el = page.wait_for_selector("iframe[src*='challenges.cloudflare.com']", timeout=10000)
    print("Found iframe element:", iframe_el)
    bb = iframe_el.bounding_box()
    print("Bounding box:", bb)
    if bb:
        # Click the checkbox inside the widget
        click_x = bb["x"] + 30
        click_y = bb["y"] + bb["height"] / 2
        print(f"Clicking at ({click_x}, {click_y})...")
        page.mouse.click(click_x, click_y)
        
        # Wait up to 10s for token
        for s in range(10):
            time.sleep(1)
            token = page.evaluate("() => window.FreegenSession && window.FreegenSession.get ? window.FreegenSession.get() : null")
            print(f"[{s}s] Token check: {token}")
            if token and not isinstance(token, dict) and len(str(token)) > 10:
                print("TOKEN ACQUIRED:", str(token)[:50])
                break
                
    page.screenshot(path=r"E:\Open-Generative-AI-main\AutoImageFlow\turnstile_click_result.png")
    b.close()
