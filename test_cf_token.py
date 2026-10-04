from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    b = p.chromium.launch_persistent_context(
        user_data_dir=r"E:\Temp\pw-test2",
        headless=False,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        ignore_default_args=["--enable-automation"],
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = b.pages[0] if b.pages else b.new_page()
    page.goto("https://freegen.app", wait_until="domcontentloaded")
    time.sleep(3)
    
    token = page.evaluate("""async () => {
        try {
            return await window.FreegenSession.get();
        } catch(e) {
            return 'ERR: ' + e;
        }
    }""")
    print("Token result:", token[:60] if token else "None")
    b.close()
