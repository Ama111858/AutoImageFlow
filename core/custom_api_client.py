import urllib.request
import urllib.error
import json
import os
import base64
import re
from utils.logger import get_logger

logger = get_logger()

class CustomAPIClient:
    def __init__(self, config, download_folder):
        self.config = config
        self.api_url = self.config.get("api_url", "")
        self.api_key = self.config.get("api_key", "")
        self.model_name = self.config.get("model_name", "")
        self.download_folder = download_folder

    def startup(self, progress_callback=None):
        if progress_callback:
            progress_callback(10, "Custom API Client Ready")

    def generate_and_download(self, prompt, auto_name, auto_download, progress_callback, negative_prompt=None, aspect_ratio="1:1", **kwargs):
        if not self.api_url:
            progress_callback(0, "Error: Custom API URL is not set.")
            return False

        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # Standard OpenAI compatible payload
        payload = {
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024"
        }
        if self.model_name:
            payload["model"] = self.model_name

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(self.api_url, data=data, headers=headers, method="POST")

        try:
            progress_callback(30, "Sending request to Custom API...")
            response = urllib.request.urlopen(req, timeout=120)
            result = json.loads(response.read())

            progress_callback(70, "Response received, processing...")

            if "data" in result and len(result["data"]) > 0:
                image_data_obj = result["data"][0]
                
                # Check for b64_json or url
                image_bytes = None
                if "b64_json" in image_data_obj:
                    image_bytes = base64.b64decode(image_data_obj["b64_json"])
                elif "url" in image_data_obj:
                    image_url = image_data_obj["url"]
                    img_req = urllib.request.Request(image_url)
                    img_res = urllib.request.urlopen(img_req, timeout=60)
                    image_bytes = img_res.read()
                
                else:
                    logger.error("Custom API Error: No valid image format (b64_json or url) found in response data.")
                    if progress_callback:
                        progress_callback(0, "Error: No valid image found in response.")
                    return False

                if auto_download:
                    if auto_name:
                        import uuid
                        safe_prompt = re.sub(r'[\\/*?:"<>|\n\r\t]', "", prompt[:30]).replace(' ', '_')
                        filename = f"custom_{str(uuid.uuid4())[:6]}_{safe_prompt}.png"
                    else:
                        import uuid
                        filename = f"custom_{str(uuid.uuid4())[:6]}.png"
                    
                    save_path = os.path.join(self.download_folder, filename)
                    with open(save_path, "wb") as f:
                        f.write(image_bytes)
                    progress_callback(100, f"Downloaded: {filename}")
                else:
                    progress_callback(100, "Done (No auto-download config)")
                
                return True
            else:
                err_msg = result.get("error", {}).get("message", "Unknown error")
                logger.error(f"Custom API Error Response: {err_msg}")
                if progress_callback:
                    progress_callback(0, f"API Error: {err_msg[:50]}...")
                return False

        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8', errors='ignore')
            logger.error(f"Custom API HTTP Error {e.code}: {err_body}")
            if progress_callback:
                progress_callback(0, f"HTTP Error {e.code}")
            return False
        except Exception as e:
            logger.error(f"Custom API Request Error: {e}")
            if progress_callback:
                progress_callback(0, f"Request Error: {e}")
            return False

    def shutdown(self):
        pass
