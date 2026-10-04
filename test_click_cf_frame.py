from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    b = p.chromium.launch_persistent_context(
        r"E:\Temp\playwright-artifacts",
        headless=False,
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = b.pages[0] if b.pages else b.new_page()
    page.goto("https://freegen.app", wait_until="domcontentloaded")
    time.sleep(3)
    
    page.fill("#prompt", "A futuristic city with flying cars")
    print("Triggering generation to activate Turnstile...")
    page.click("#generateBtn", force=True)
    time.sleep(2)
    
    for f in page.frames:
        print(f"Frame URL: {f.url}")
        if "challenges.cloudflare.com" in f.url:
            print("Found Turnstile Frame!")
            # Try to get elements inside
            try:
                # Find all buttons or checkboxes or labels or spans
                els = f.locator("input, label, [role='checkbox'], div, span").all()
                print(f"Elements inside CF frame: {len(els)}")
                for e in els[:15]:
                    tag = e.evaluate("el => el.tagName")
                    cls = e.get_attribute("class") or ""
                    role = e.get_attribute("role") or ""
                    box = e.bounding_box()
                    print(f"  Tag: {tag}, class: '{cls}', role: '{role}', bb: {box}")
                    if "checkbox" in role or "checkbox" in cls or tag.lower() == "input":
                        print("  --> Clicking checkbox element!")
                        e.click()
                        time.sleep(3)
                        break
            except Exception as ex:
                print("Error inspecting CF frame:", ex)
                
    time.sleep(5)
    page.screenshot(path=r"E:\Open-Generative-AI-main\AutoImageFlow\cf_click_try.png")
    b.close()
