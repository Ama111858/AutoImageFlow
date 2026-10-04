from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    b = p.chromium.launch_persistent_context(r"E:\Temp\playwright-artifacts", headless=False)
    page = b.pages[0] if b.pages else b.new_page()
    page.goto("https://freegen.app", wait_until="domcontentloaded")
    time.sleep(3)
    page.click("#generateBtn", force=True)
    time.sleep(4)
    
    print(f"Total page frames: {len(page.frames)}")
    for idx, f in enumerate(page.frames):
        print(f"--- Frame {idx}: {f.url[:80]} ---")
        try:
            html = f.evaluate("() => document.documentElement.outerHTML")
            print(f"  Length: {len(html)}")
            if "checkbox" in html.lower() or "turnstile" in html.lower() or "verify" in html.lower():
                print("  Matches challenge keywords!")
                # Find interactive elements
                tags = f.evaluate("""() => {
                    return Array.from(document.querySelectorAll('*')).filter(el => {
                        const tag = el.tagName.toLowerCase();
                        return tag === 'input' || tag === 'label' || tag === 'span' || tag === 'button' || el.getAttribute('role') === 'checkbox';
                    }).map(el => ({
                        tag: el.tagName,
                        type: el.type || '',
                        id: el.id || '',
                        class: el.className || '',
                        role: el.getAttribute('role') || '',
                        text: el.innerText ? el.innerText.slice(0, 30) : ''
                    }));
                }""")
                print("  Interactive elements:", tags)
        except Exception as e:
            print("  Evaluate error:", e)
            
    b.close()
