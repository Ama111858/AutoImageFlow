from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    b = p.chromium.launch_persistent_context(r"E:\Temp\playwright-artifacts", headless=False)
    page = b.pages[0] if b.pages else b.new_page()
    page.goto("https://freegen.app", wait_until="domcontentloaded")
    time.sleep(4)
    page.click("#generateBtn", force=True)
    time.sleep(5)
    
    iframes = page.query_selector_all("iframe")
    print("Total iframes found:", len(iframes))
    for idx, ifr in enumerate(iframes):
        src = ifr.get_attribute("src") or ""
        visible = ifr.is_visible()
        bb = ifr.bounding_box()
        print(f"[{idx}] src: {src[:70]}, visible: {visible}, bb: {bb}")
        
    widget = page.query_selector("#turnstileWidget")
    if widget:
        print("turnstileWidget bb:", widget.bounding_box())
        print("turnstileWidget innerHTML:", page.inner_html("#turnstileWidget")[:300])

    b.close()
