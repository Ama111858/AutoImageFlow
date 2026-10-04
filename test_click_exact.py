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
    time.sleep(3)
    
    page.fill("#prompt", "A cinematic cute baby panda in high definition")
    print("Clicking Generate...")
    page.click("#generateBtn", force=True)
    
    # Loop and monitor turnstileWidget every 200ms
    clicked = False
    for i in range(100): # 20 seconds
        time.sleep(0.2)
        widget = page.query_selector("#turnstileWidget")
        if widget and widget.is_visible():
            bb = widget.bounding_box()
            if bb and bb["width"] > 100 and bb["height"] > 40:
                print(f"[{i*0.2:.1f}s] Turnstile widget is visible! BB: {bb}")
                # Wait 500ms for iframe inside to settle
                time.sleep(0.5)
                # Recalculate bb
                bb = widget.bounding_box()
                click_x = bb["x"] + 24
                click_y = bb["y"] + 32
                print(f"Clicking Turnstile checkbox at ({click_x}, {click_y})...")
                # Move mouse and click like a human
                page.mouse.move(click_x, click_y)
                time.sleep(0.1)
                page.mouse.down()
                time.sleep(0.15)
                page.mouse.up()
                clicked = True
                print("Clicked!")
                break
                
    if not clicked:
        print("Widget was never detected as visible in 20s.")
        
    time.sleep(3)
    page.screenshot(path=r"E:\Open-Generative-AI-main\AutoImageFlow\after_exact_click.png")
    
    # Wait and check for generation
    print("Watching for generation results...")
    for s in range(40):
        time.sleep(1)
        btn = page.query_selector("#generateBtn")
        btn_text = btn.inner_text() if btn else ""
        imgs = page.query_selector_all("#imageContainer img")
        alerts = [a.inner_text() for a in page.query_selector_all(".alert, .error, [role='alert']") if a.inner_text()]
        print(f"[{s}s] btnText: '{btn_text}', imgs: {len(imgs)}, alerts: {alerts}")
        if imgs:
            for img in imgs:
                src = img.get_attribute("src") or ""
                print(">>> IMAGE FOUND! <<< src:", src[:80])
            break
            
    page.screenshot(path=r"E:\Open-Generative-AI-main\AutoImageFlow\exact_final.png")
    b.close()
