import time
import os
import sys
from playwright.sync_api import sync_playwright

artifacts_dir = r"E:\Temp\playwright-artifacts"
os.makedirs(artifacts_dir, exist_ok=True)

print("Starting Playwright...", flush=True)
with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir=artifacts_dir,
        headless=False,
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = browser.pages[0] if browser.pages else browser.new_page()

    page.on("console", lambda msg: print(f"CONSOLE: [{msg.type}] {msg.text}", flush=True))
    page.on("response", lambda r: print(f"NET: {r.status} {r.url[:70]}", flush=True) if "generate" in r.url or "api" in r.url or "sign" in r.url or "session" in r.url or "adapter" in r.url else None)

    print("Navigating to https://freegen.app...", flush=True)
    page.goto("https://freegen.app", wait_until="domcontentloaded", timeout=60000)
    time.sleep(4)

    prompt_sel = "#prompt"
    gen_btn = "#generateBtn"
    img_out = "#imageContainer"

    print("Waiting for prompt selector...", flush=True)
    page.wait_for_selector(prompt_sel, state="visible", timeout=15000)
    
    print("Filling prompt...", flush=True)
    page.fill(prompt_sel, "A beautiful glowing crystal flower in a dark cave, highly detailed")

    # Check Turnstile token
    for i in range(10):
        token_state = page.evaluate("() => ({ hasTurnstile: !!window.turnstile, hasSession: !!window.FreegenSession })")
        print(f"Token check {i}: {token_state}", flush=True)
        time.sleep(1)

    print("Clicking Generate button...", flush=True)
    page.click(gen_btn, force=True)

    print("Waiting and inspecting state...", flush=True)
    for s in range(30):
        time.sleep(1)
        # Check what is happening inside imageContainer or if any modals/overlays exist
        state = page.evaluate("""() => {
            const container = document.querySelector('#imageContainer');
            const imgs = container ? Array.from(container.querySelectorAll('img')).map(i => ({ src: i.src ? i.src.slice(0, 60) : '', width: i.naturalWidth, height: i.naturalHeight, complete: i.complete })) : [];
            const alerts = Array.from(document.querySelectorAll('.alert, .error, [role="alert"]')).map(a => a.innerText);
            const btnText = document.querySelector('#generateBtn') ? document.querySelector('#generateBtn').innerText : '';
            const btnDisabled = document.querySelector('#generateBtn') ? document.querySelector('#generateBtn').disabled : false;
            return { imgs, alerts, btnText, btnDisabled, containerHTML: container ? container.innerHTML.slice(0, 200) : '' };
        }""")
        print(f"[{s}s] State: {state}", flush=True)
        if state['imgs'] and any(img['complete'] and img['width'] > 100 for img in state['imgs']):
            print("FOUND GENERATED IMAGE!", flush=True)
            break

    screenshot_path = r"E:\Open-Generative-AI-main\AutoImageFlow\step_by_step.png"
    page.screenshot(path=screenshot_path)
    print(f"Screenshot saved to {screenshot_path}", flush=True)
    browser.close()
