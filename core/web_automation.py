from playwright.sync_api import sync_playwright
import os
import uuid
import time
import base64
import re
from utils.logger import get_logger

logger = get_logger()

class WebAutomationRunner:
    def _try_solve_turnstile(self):
        if getattr(self, '_turnstile_clicked', False):
            return False
        try:
            widget = self.page.query_selector("#turnstileWidget")
            if widget and widget.is_visible():
                bb = widget.bounding_box()
                if bb and bb["width"] > 100 and bb["height"] > 40:
                    logger.info(f"Turnstile challenge detected ({bb['width']}x{bb['height']}). Waiting 500ms to settle...")
                    self.page.wait_for_timeout(500)
                    bb = widget.bounding_box()
                    click_x = bb["x"] + 24
                    click_y = bb["y"] + 32
                    logger.info(f"Clicking Turnstile checkbox at ({click_x}, {click_y})")
                    self.page.mouse.move(click_x, click_y)
                    self.page.wait_for_timeout(100)
                    self.page.mouse.down()
                    self.page.wait_for_timeout(150)
                    self.page.mouse.up()
                    self._turnstile_clicked = True
                    logger.info("Turnstile checkbox clicked successfully.")
                    self.page.wait_for_timeout(1500)
                    return True
        except Exception as e:
            logger.warning(f"Error checking/clicking Turnstile: {e}")
        return False

    def _wait_for_challenge_and_ads(self, progress_callback=None):
        logger.info("Checking browser state for challenges or ads...")
        start_time = time.time()
        was_blocked = False
        
        while time.time() - start_time < 120:
            try:
                # Check and solve Cloudflare Turnstile if present
                if self._try_solve_turnstile():
                    was_blocked = True
                    self.page.wait_for_timeout(2000)
                    continue

                is_blocked = False
                block_reason = ""
                
                title = self.page.title().lower()
                if "just a moment" in title or "attention required" in title or "security check" in title:
                    is_blocked = True
                    block_reason = "Cloudflare security check"
                
                if not is_blocked:
                    # Cloudflare / Captcha elements
                    cf_elements = [
                        "#challenge-running", "#challenge-form", ".cf-browser-verification", 
                        "iframe[title*='recaptcha']", "iframe[title*='hcaptcha']"
                    ]
                    for sel in cf_elements:
                        if self.page.query_selector(sel) and self.page.is_visible(sel):
                            is_blocked = True
                            block_reason = f"Security Challenge ({sel})"
                            break
                            
                if not is_blocked:
                    # Ad / Interstitial elements that might require watching or closing
                    ad_elements = [
                        "div[id*='ad-overlay']", "div[class*='ad-overlay']"
                    ]
                    for sel in ad_elements:
                        if self.page.query_selector(sel) and self.page.is_visible(sel):
                            is_blocked = True
                            block_reason = f"Ad overlay ({sel})"
                            break
                            
                if is_blocked:
                    was_blocked = True
                    logger.info(f"Blocked by: {block_reason}. Waiting for user or auto-completion...")
                    if progress_callback:
                        progress_callback(10, f"Waiting for {block_reason} to clear...")
                    self.page.wait_for_timeout(2000)
                else:
                    if was_blocked:
                        logger.info("Verification/Ad successfully cleared! Resuming...")
                    return True
            except Exception as e:
                logger.warning(f"Error checking browser state: {e}")
                self.page.wait_for_timeout(2000)
                
        logger.error("Timed out waiting for challenge/ad to clear.")
        return False

    def __init__(self, config, download_folder):
        self.config = config
        self.download_folder = download_folder
        self.playwright = None
        self.browser = None
        self.page = None
        self._turnstile_clicked = False

    def startup(self, progress_callback=None):
        import tempfile
        temp_dir = os.path.abspath(tempfile.gettempdir())
        artifacts_dir = os.path.join(temp_dir, "playwright-artifacts")
        
        os.makedirs(artifacts_dir, exist_ok=True)
        os.environ["TEMP"] = temp_dir
        os.environ["TMP"] = temp_dir

        logger.info(f"TEMP = {temp_dir}")
        logger.info(f"ARTIFACTS = {artifacts_dir}")

        def log(msg):
            safe_msg = str(msg).encode('ascii', errors='replace').decode('ascii')
            if progress_callback:
                try:
                    progress_callback(0, safe_msg)
                except Exception:
                    pass
            logger.info(safe_msg)

        log(f"TEMP path: {os.environ['TEMP']}")
        log(f"TMP path: {os.environ['TMP']}")
        log("Browser launching")

        # Detect system-installed Google Chrome or Edge instead of relying on missing ms-playwright Chromium
        chrome_candidates = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
        ]
        system_chrome = next((p for p in chrome_candidates if os.path.exists(p)), None)

        launch_kwargs = {
            "headless": False,
            "downloads_path": temp_dir,
            "args": ["--disable-blink-features=AutomationControlled"]
        }
        if system_chrome:
            launch_kwargs["executable_path"] = system_chrome
        else:
            launch_kwargs["channel"] = "chrome"

        self.playwright = sync_playwright().start()
        try:
            self.browser = self.playwright.chromium.launch_persistent_context(
                user_data_dir=artifacts_dir,
                **launch_kwargs
            )
            log(f"Browser executable path: {system_chrome or getattr(self.playwright.chromium, 'executable_path', 'chrome')}")
            log("Launch arguments: headless=False, downloads_path=" + temp_dir)
            log(f"Profile path: {artifacts_dir}")
            log("Webdriver path: None (Playwright uses CDP, no webdriver)")
        except Exception:
            import traceback
            log("Browser launch error, retrying...")
            temp_profile = os.path.join(temp_dir, f"temp_profile_{uuid.uuid4().hex[:6]}")
            self.browser = self.playwright.chromium.launch_persistent_context(
                user_data_dir=temp_profile,
                **launch_kwargs
            )

        self.page = self.browser.pages[0] if self.browser.pages else self.browser.new_page()
        log("Browser launched")
        
        url = self.config.get("url", "").strip()
        if not url:
            raise ValueError("URL is missing from configuration.")
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url

        log(f"Navigating to {url}")
        
        selectors = self.config.get("selectors", {})
        prompt_sel = selectors.get("prompt_input") or "#prompt"
        gen_btn_sel = selectors.get("generate_btn") or "#generateBtn"
        
        max_retries = 1
        for attempt in range(max_retries + 1):
            try:
                self.page.goto(url, timeout=120000, wait_until="domcontentloaded")
                log("Consent handled")
                log("DOM loaded")
                
                self._wait_for_challenge_and_ads(progress_callback)
                
                try:
                    self.page.wait_for_selector(prompt_sel, state="attached", timeout=90000)
                    log("Prompt selector found")
                except Exception:
                    raise Exception(f"Timeout: selector '{prompt_sel}' not found")
                    
                try:
                    self.page.wait_for_selector(gen_btn_sel, state="attached", timeout=90000)
                    log("Generate selector found")
                except Exception:
                    raise Exception(f"Timeout: selector '{gen_btn_sel}' not found")
                
                break
            except Exception as e:
                if attempt < max_retries:
                    err_msg = f"Web Automation Error:\n{str(e)}\n\nRetrying once..."
                    log(f"GUI_ERROR_RETRY: {err_msg}")
                else:
                    err_msg = f"Navigation failed after retries: {str(e)}."
                    log(err_msg)
                    raise Exception(err_msg)

    def generate_and_download(self, prompt, auto_name, auto_download, progress_callback, negative_prompt=None, aspect_ratio="1:1", **kwargs):
        self._turnstile_clicked = False
        selectors = self.config.get("selectors", {})
        prompt_sel = selectors.get("prompt_input")
        gen_btn = selectors.get("generate_btn")
        img_out = selectors.get("image_output")
        dl_btn = selectors.get("download_btn")

        if not all([prompt_sel, gen_btn, img_out]):
            logger.error("Missing essential selectors in config.")
            return False

        try:
            logger.info("Queue Start")
            self._wait_for_challenge_and_ads(progress_callback)
            
            # 1. Input prompt
            self.page.fill(prompt_sel, prompt)
            logger.info("Prompt Sent")
            progress_callback(20, "Prompt Sent")
            
            # Select Aspect Ratio
            if aspect_ratio:
                try:
                    logger.info(f"Selecting Aspect Ratio: {aspect_ratio}")
                    # Try exact match first
                    loc = self.page.get_by_text(aspect_ratio, exact=True).first
                    
                    if loc.count() > 0:
                        tag_name = loc.evaluate("el => el.tagName").lower()
                        if tag_name == "option":
                            parent_select = loc.locator("xpath=ancestor::select").first
                            if parent_select.count() > 0:
                                val = loc.get_attribute("value")
                                parent_select.select_option(val, timeout=3000)
                                logger.info(f"Aspect ratio {aspect_ratio} selected via dropdown.")
                            else:
                                loc.click(timeout=3000, force=True)
                                logger.info(f"Aspect ratio {aspect_ratio} clicked directly (option without select).")
                        else:
                            loc.click(timeout=3000, force=True)
                            logger.info(f"Aspect ratio {aspect_ratio} clicked directly.")
                    else:
                        # Fallback to partial match
                        fallback = self.page.locator(f"//*[contains(text(), '{aspect_ratio}')]").first
                        if fallback.count() > 0:
                            tag_name = fallback.evaluate("el => el.tagName").lower()
                            if tag_name == "option":
                                parent_select = fallback.locator("xpath=ancestor::select").first
                                if parent_select.count() > 0:
                                    val = fallback.get_attribute("value")
                                    parent_select.select_option(val, timeout=3000)
                                    logger.info(f"Aspect ratio {aspect_ratio} selected via fallback dropdown.")
                                else:
                                    fallback.click(timeout=3000, force=True)
                                    logger.info(f"Aspect ratio {aspect_ratio} clicked via fallback partial match.")
                            else:
                                fallback.click(timeout=3000, force=True)
                                logger.info(f"Aspect ratio {aspect_ratio} clicked via fallback partial match.")
                        else:
                            logger.warning(f"Aspect ratio {aspect_ratio} not found on page.")
                except Exception as e:
                    logger.warning(f"Could not click aspect ratio {aspect_ratio}: {e}")
            
            # Get old image state to avoid grabbing a placeholder
            old_srcs = set()
            try:
                old_imgs = self.page.query_selector_all(f"{img_out} img")
                for img in old_imgs:
                    src = img.get_attribute("src")
                    if src:
                        old_srcs.add(src)
            except Exception:
                pass
            
            # 2. Click Generate
            time.sleep(1.0)
            self.page.click(gen_btn, force=True)
            logger.info("Generate button clicked.")
            progress_callback(40, "Generating image...")

            # Monitor for Turnstile challenge (up to 12 seconds)
            for _ in range(40):
                if self._try_solve_turnstile():
                    logger.info("Turnstile solved after click.")
                    break
                self.page.wait_for_timeout(300)

            # 3. Wait for new image
            img_element = None
            start_time = time.time()
            timeout = 180  # Up to 3 minutes
            reclicked_after_turnstile = False
            
            while time.time() - start_time < timeout:
                if not getattr(self, '_turnstile_clicked', False):
                    self._try_solve_turnstile()
                    
                elapsed = int(time.time() - start_time)
                current_imgs = []
                try:
                    current_imgs = self.page.query_selector_all(f"{img_out} img")
                    for img in current_imgs:
                        current_src = img.get_attribute("src")
                        # Look for a valid src that wasn't there before
                        if current_src and current_src not in old_srcs and current_src != "" and not current_src.startswith("data:image/gif"):
                            # Validate that it's a fully loaded, real image (not a 1x1 ad pixel or placeholder)
                            is_valid = self.page.evaluate('(img) => img.complete && (img.naturalWidth > 50 || img.width > 50)', img)
                            if is_valid:
                                img_element = img
                                break
                    if img_element:
                        break
                except Exception:
                    pass
                    
                # Periodic status logging and recovery
                if elapsed > 0 and elapsed % 3 == 0:
                    try:
                        b_text = self.page.inner_text(gen_btn).strip()
                        alerts = [a.inner_text().strip() for a in self.page.query_selector_all(".alert, .error, [role='alert']") if a.inner_text().strip()]
                        logger.info(f"[{elapsed}s] Button: '{b_text}', Imgs: {len(current_imgs)}, Alerts: {alerts}")
                        
                        # If turnstile was clicked and button is idle ('Generate'), re-click Generate
                        if getattr(self, '_turnstile_clicked', False) and not reclicked_after_turnstile and elapsed > 8:
                            if "generating" not in b_text.lower():
                                logger.info("Turnstile was solved but button is idle ('Generate'). Clicking Generate again...")
                                self.page.click(gen_btn, force=True)
                                reclicked_after_turnstile = True
                    except Exception as e:
                        logger.debug(f"Status check error: {e}")
                    
                self.page.wait_for_timeout(1000)

            if not img_element:
                try:
                    debug_shot = os.path.join(self.download_folder, "timeout_debug.png")
                    self.page.screenshot(path=debug_shot)
                    logger.info(f"Saved timeout screenshot to {debug_shot}")
                except Exception:
                    pass
                raise Exception("Timeout waiting for new image generation")
                
            logger.info("API Response Received")
            progress_callback(80, "Image detected")

            # 4. Download
            if auto_download:
                if auto_name:
                    safe_prompt = re.sub(r'[\\/*?:"<>|\n\r\t]', "", prompt[:30]).replace(' ', '_')
                    filename = f"{str(uuid.uuid4())[:6]}_{safe_prompt}.png"
                else:
                    filename = f"gen_{str(uuid.uuid4())[:6]}.png"
                save_path = os.path.join(self.download_folder, filename)

                logger.info("Saving image")
                progress_callback(90, "Saving image")

                if dl_btn:
                    with self.page.expect_download(timeout=60000) as download_info:
                        self.page.click(dl_btn)
                    download = download_info.value
                    
                    if not auto_name:
                        filename = download.suggested_filename
                        save_path = os.path.join(self.download_folder, filename)
                    
                    download.save_as(save_path)
                else:
                    try:
                        self.page.wait_for_function("img => img.complete", arg=img_element, timeout=30000)
                    except Exception:
                        pass
                    
                    downloaded_directly = False
                    try:
                        img_src = img_element.get_attribute("src")
                        if img_src:
                            if img_src.startswith("http"):
                                response = self.page.context.request.get(img_src)
                                with open(save_path, "wb") as f:
                                    f.write(response.body())
                                downloaded_directly = True
                                logger.info("Downloaded image directly via URL")
                            elif img_src.startswith("data:image"):
                                header, encoded = img_src.split(",", 1)
                                with open(save_path, "wb") as f:
                                    f.write(base64.b64decode(encoded))
                                downloaded_directly = True
                                logger.info("Saved base64 image directly")
                            elif img_src.startswith("blob:"):
                                b64_data = self.page.evaluate('''async (url) => {
                                    const response = await fetch(url);
                                    const blob = await response.blob();
                                    return new Promise((resolve) => {
                                        const reader = new FileReader();
                                        reader.onloadend = () => resolve(reader.result);
                                        reader.readAsDataURL(blob);
                                    });
                                }''', img_src)
                                header, encoded = b64_data.split(",", 1)
                                with open(save_path, "wb") as f:
                                    f.write(base64.b64decode(encoded))
                                downloaded_directly = True
                                logger.info("Downloaded blob image directly via JS")
                    except Exception as e:
                        logger.error(f"Direct download failed: {e}. Falling back to screenshot.")

                    if not downloaded_directly:
                        try:
                            # Do NOT hide overlays/iframes here, as it breaks legitimate ad flows and anti-adblock detection for subsequent generations!
                            pass
                        except Exception as e:
                            logger.error(f"Failed to process overlays: {e}")
                        
                        try:
                            # Scroll into view before screenshot
                            img_element.scroll_into_view_if_needed(timeout=5000)
                            img_element.screenshot(path=save_path, timeout=10000)
                        except Exception as e:
                            logger.error(f"Screenshot failed: {e}")
                            raise Exception(f"Failed to save image to disk: {e}")

                logger.info("Image Saved")
                logger.info(f"File saved path: {save_path}")
                
                # Verify actual file existence
                time.sleep(1)
                
                if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
                    logger.info("Queue Next Item")
                    progress_callback(100, "Queue continuing")
                    
                    try:
                        self.page.reload(wait_until="domcontentloaded", timeout=60000)
                    except Exception as e:
                        logger.error(f"Reload failed on success: {e}")
                        
                    return True
                else:
                    logger.error("Download failed")
                    progress_callback(100, "Failed")
                    
                    try:
                        self.page.reload(wait_until="domcontentloaded", timeout=60000)
                    except Exception as e:
                        logger.error(f"Reload failed on download failure: {e}")
                        
                    return False
            else:
                progress_callback(100, "Done (No auto-download config)")
                
                try:
                    self.page.reload(wait_until="domcontentloaded", timeout=60000)
                except Exception as e:
                    logger.error(f"Reload failed on skip download: {e}")
                    
                return True
        except Exception as e:
            logger.error(f"WebAutomation Error: {e}")
            try:
                self.page.reload(wait_until="domcontentloaded", timeout=60000)
            except Exception as reload_err:
                logger.error(f"Browser recovery failed: {reload_err}. Attempting full restart...")
                try:
                    self.shutdown()
                    self.startup(progress_callback)
                except Exception as startup_err:
                    logger.error(f"Full restart failed: {startup_err}")
            return False

    def shutdown(self):
        try:
            if self.browser:
                self.browser.close()
        except Exception as e:
            logger.error(f"Browser close error: {e}")
            
        try:
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            logger.error(f"Playwright stop error: {e}")
