import time
import os
from playwright.sync_api import sync_playwright

artifacts_dir = r"E:\Temp\playwright-artifacts"
os.makedirs(artifacts_dir, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir=artifacts_dir,
        headless=True,
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = browser.pages[0] if browser.pages else browser.new_page()

    console_logs = []
    page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
    
    net_logs = []
    page.on("response", lambda r: net_logs.append(f"RESP {r.status} {r.url[:80]}"))

    print("Navigating to https://freegen.app...")
    page.goto("https://freegen.app", wait_until="domcontentloaded")
    time.sleep(3)

    print(f"Title: {page.title()}")
    prompt_sel = "#prompt"
    gen_btn_sel = "#generateBtn"

    page.wait_for_selector(prompt_sel, state="visible", timeout=10000)
    page.fill(prompt_sel, "A magical blue dragon over snowy mountains")
    print("Filled prompt.")

    # Check if adblock locked
    is_locked = page.evaluate("() => document.documentElement.classList.contains('adblock-locked')")
    print(f"Is adblock locked? {is_locked}")

    # Check if turnstile exists
    has_turnstile = page.evaluate("() => !!window.turnstile")
    print(f"Has turnstile? {has_turnstile}")
    
    # Check session
    session_val = page.evaluate("async () => { try { return await window.FreegenSession.get(); } catch(e) { return 'ERR: ' + e; } }")
    print(f"FreegenSession token: {str(session_val)[:50] if session_val else 'None'}")

    print("Clicking Generate...")
    page.click(gen_btn_sel, force=True)
    
    time.sleep(10)
    
    screenshot_path = r"E:\Open-Generative-AI-main\AutoImageFlow\freegen_debug.png"
    page.screenshot(path=screenshot_path)
    print(f"Screenshot saved to {screenshot_path}")

    # Check image container
    img_container_html = page.inner_html("#imageContainer")
    print(f"ImageContainer HTML: {img_container_html[:300]}")

    print("\nRecent console logs:")
    for log in console_logs[-15:]:
        print("  ", log)

    print("\nRecent network responses:")
    for net in net_logs[-15:]:
        print("  ", net)

    browser.close()
