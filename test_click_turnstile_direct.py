from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    b = p.chromium.launch_persistent_context(r"E:\Temp\playwright-artifacts", headless=False)
    page = b.pages[0] if b.pages else b.new_page()
    page.goto("https://freegen.app", wait_until="domcontentloaded")
    time.sleep(4)
    page.fill("#prompt", "A cute baby panda eating bamboo in sunlight")
    page.click("#generateBtn", force=True)
    time.sleep(2)
    
    # Check turnstileWidget bounding box
    widget = page.query_selector("#turnstileWidget")
    if widget:
        bb = widget.bounding_box()
        print("Widget BB:", bb)
        if bb and bb["width"] > 50:
            click_x = bb["x"] + 30
            click_y = bb["y"] + bb["height"] / 2
            print(f"Clicking at ({click_x}, {click_y})...")
            page.mouse.click(click_x, click_y)
            time.sleep(4)
            
    page.screenshot(path=r"E:\Open-Generative-AI-main\AutoImageFlow\after_widget_click.png")
    
    # Observe generation
    for s in range(30):
        time.sleep(1)
        btn = page.query_selector("#generateBtn")
        btn_text = btn.inner_text() if btn else ""
        imgs = page.query_selector_all("#imageContainer img")
        print(f"[{s}s] btnText: '{btn_text}', imgs count: {len(imgs)}")
        if imgs:
            for img in imgs:
                src = img.get_attribute("src")
                print(f"  img src: {src[:60] if src else ''}")
            break
            
    page.screenshot(path=r"E:\Open-Generative-AI-main\AutoImageFlow\after_widget_gen.png")
    b.close()
