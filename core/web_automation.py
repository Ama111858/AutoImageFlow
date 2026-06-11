from playwright.sync_api import sync_playwright
import os
import uuid
import time
import base64
import re
from utils.logger import get_logger

logger = get_logger()

class WebAutomationRunner:
    def __init__(self, config, download_folder):
        self.config = config
        self.download_folder = download_folder
        self.playwright = None
        self.browser = None
        self.page = None

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
            if progress_callback:
                progress_callback(0, msg)
            logger.info(msg)

        log(f"TEMP path: {os.environ['TEMP']}")
        log(f"TMP path: {os.environ['TMP']}")
        log("Browser launching")

        self.playwright = sync_playwright().start()
        try:
            self.browser = self.playwright.chromium.launch_persistent_context(
                user_data_dir=artifacts_dir,
                headless=False,
                downloads_path=temp_dir
            )
            log(f"Browser executable path: {self.playwright.chromium.executable_path}")
            log("Launch arguments: headless=False, downloads_path=" + temp_dir)
            log(f"Profile path: {artifacts_dir}")
            log("Webdriver path: None (Playwright uses CDP, no webdriver)")
        except Exception:
            import traceback
            log("Browser crashed on launch! Traceback:")
            log(traceback.format_exc())
            
            temp_profile = os.path.join(temp_dir, f"temp_profile_{uuid.uuid4().hex[:6]}")
            log(f"Browser executable path: {self.playwright.chromium.executable_path}")
            log("Launch arguments: headless=False, user-data-dir=" + temp_profile)
            log(f"Profile path: {temp_profile}")
            log("Webdriver path: None (Playwright uses CDP, no webdriver)")
            
            log(f"Launching with clean temporary profile: {temp_profile}")
            self.browser = self.playwright.chromium.launch_persistent_context(
                user_data_dir=temp_profile,
                headless=False,
                downloads_path=temp_dir
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
            # 1. Input prompt
            self.page.fill(prompt_sel, prompt)
            logger.info("Prompt Sent")
            progress_callback(20, "Prompt Sent")
            
            # Select Aspect Ratio
            if aspect_ratio:
                try:
                    logger.info(f"Selecting Aspect Ratio: {aspect_ratio}")
                    ar_element = self.page.get_by_text(aspect_ratio, exact=True).first
                    if ar_element:
                        ar_element.click(timeout=3000)
                        logger.info(f"Aspect ratio {aspect_ratio} selected.")
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
            self.page.click(gen_btn)
            progress_callback(40, "Generating image...")

            # 3. Wait for new image
            img_element = None
            start_time = time.time()
            timeout = 60
            
            while time.time() - start_time < timeout:
                try:
                    current_imgs = self.page.query_selector_all(f"{img_out} img")
                    for img in current_imgs:
                        current_src = img.get_attribute("src")
                        # Look for a valid src that wasn't there before
                        if current_src and current_src not in old_srcs and current_src != "":
                            img_element = img
                            break
                    if img_element:
                        break
                except Exception:
                    pass
                self.page.wait_for_timeout(1000)

            if not img_element:
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
                            self.page.evaluate('''() => {
                                const overlaySelectors = [
                                    'iframe', '[class*="ad-"]', '[class*="ads-"]', '[id*="ad-"]', 
                                    '[id*="ads-"]', '[class*="banner"]', '[id*="banner"]',
                                    '[class*="cookie"]', '[id*="cookie"]', '[class*="popup"]', 
                                    '[id*="popup"]', '[class*="sticky"]', '[id*="sticky"]'
                                ];
                                document.querySelectorAll(overlaySelectors.join(',')).forEach(el => {
                                    try { el.style.display = 'none'; } catch(e) {}
                                });
                            }''')
                        except Exception as e:
                            logger.error(f"Failed to hide overlays: {e}")
                        
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
