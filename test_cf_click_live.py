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

    page.fill("#prompt", "A cute baby panda eating bamboo in sunlight")
    print("Filled prompt. Clicking Generate to trigger Turnstile challenge...")
    page.click("#generateBtn", force=True)

    print("Monitoring for iframe[src*='cloudflare']...")
    for i in range(30):
        time.sleep(1)
        el = page.query_selector("iframe[src*='cloudflare']")
        if el and el.is_visible():
            bb = el.bounding_box()
            print(f"[{i}s] Cloudflare iframe IS VISIBLE! bb={bb}")
            if bb and bb["width"] > 50:
                # Click the checkbox inside the turnstile widget
                # The checkbox in Cloudflare Turnstile widget is at x ~ 28px, y ~ 32px
                click_x = bb["x"] + 28
                click_y = bb["y"] + 32
                print(f"Clicking at ({click_x}, {click_y})...")
                page.mouse.click(click_x, click_y)
                time.sleep(3)
                
                # Take screenshot immediately after click
                page.screenshot(path=r"E:\Open-Generative-AI-main\AutoImageFlow\cf_clicked.png")
                break
        else:
            print(f"[{i}s] iframe visible: {el.is_visible() if el else 'no el'}")

    # Now observe what happens to generation!
    print("Waiting for generation result...")
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

    page.screenshot(path=r"E:\Open-Generative-AI-main\AutoImageFlow\cf_final.png")
    b.close()
