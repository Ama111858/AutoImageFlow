import os
import uuid
import time
import re
import urllib.request
import urllib.error
import json
from utils.logger import get_logger

logger = get_logger()

class HordeClient:
    def __init__(self, config, download_folder):
        self.config = config
        self.api_key = self.config.get("api_key", "").strip() or "0000000000"
        self.model_name = self.config.get("model_selection", "DreamShaper")
        self.download_folder = download_folder
        self.HORDE_API = "https://aihorde.net/api/v2"

    def startup(self, progress_callback=None):
        if progress_callback:
            progress_callback(10, "AI Horde Client Ready")

    def generate_and_download(self, prompt, auto_name, auto_download, progress_callback, negative_prompt=None, aspect_ratio="1:1", should_stop=None, **kwargs):
        headers = {
            "Content-Type": "application/json",
            "apikey": self.api_key,
            "Client-Agent": "AutoImageFlow:1.0:local",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        # Parse aspect ratio to width/height
        mapping = {
            "9:16": (512, 768),
            "16:9": (768, 512),
            "1:1":  (512, 512),
            "4:3":  (640, 512),
            "3:4":  (512, 640),
        }
        width, height = mapping.get(aspect_ratio, (512, 512))
        
        # If the user has a real key, we can increase the resolution.
        # But for anonymous key (0000000000), we MUST stay at 512-based sizes to avoid KudosUpfront 403.
        if self.api_key != "0000000000":
            # Just double the size for better quality if they have an account
            if aspect_ratio == "1:1": width, height = 1024, 1024
            elif aspect_ratio == "16:9": width, height = 1024, 576
            elif aspect_ratio == "9:16": width, height = 576, 1024
            elif aspect_ratio == "4:3": width, height = 1024, 768
            elif aspect_ratio == "3:4": width, height = 768, 1024

        payload = {
            "prompt": prompt,
            "params": {
                "sampler_name": "k_euler_a",
                "cfg_scale": 7,
                "width": width,
                "height": height,
                "steps": 20
            },
            "nsfw": False,
            "censor_nsfw": True,
            "r2": True,
            "shared": True,
            "models": [self.model_name]
        }

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(f"{self.HORDE_API}/generate/async", data=data, headers=headers, method="POST")

        try:
            progress_callback(30, "Submitting job to AI Horde...")
            response = urllib.request.urlopen(req, timeout=30)
            result = json.loads(response.read())
            
            job_id = result.get("id")
            if not job_id:
                err = result.get("message", "Unknown error submitting job")
                logger.error(f"AI Horde Submission Error: {err}")
                progress_callback(0, f"Error: {err}")
                return False

            progress_callback(40, f"Job submitted. ID: {job_id[:8]}... Polling status...")
            
            # Poll status
            max_polls = 300
            for i in range(max_polls):
                if should_stop and should_stop():
                    logger.info("Generation cancelled by user.")
                    progress_callback(0, "Cancelled.")
                    # Optionally cancel the job on horde here using DELETE /generate/status/{job_id}
                    return False
                    
                status_req = urllib.request.Request(f"{self.HORDE_API}/generate/status/{job_id}", headers=headers, method="GET")
                status_resp = urllib.request.urlopen(status_req, timeout=30)
                status_data = json.loads(status_resp.read())
                
                done = status_data.get("done", False)
                wait_time = status_data.get("wait_time", 0)
                queue_pos = status_data.get("queue_position", 0)
                
                if done:
                    generations = status_data.get("generations", [])
                    if not generations:
                        progress_callback(0, "No generations returned.")
                        return False
                        
                    img_url = generations[0].get("img")
                    if not img_url:
                        progress_callback(0, "No image URL returned.")
                        return False
                        
                    progress_callback(80, "Image generated. Downloading...")
                    
                    if auto_download:
                        if auto_name:
                            safe_prompt = re.sub(r'[\\/*?:"<>|\n\r\t]', "", prompt[:30]).replace(' ', '_')
                            filename = f"horde_{str(uuid.uuid4())[:6]}_{safe_prompt}.webp"
                        else:
                            filename = f"horde_{str(uuid.uuid4())[:6]}.webp"
                        
                        save_path = os.path.join(self.download_folder, filename)
                        
                        dl_req = urllib.request.Request(img_url)
                        dl_resp = urllib.request.urlopen(dl_req, timeout=60)
                        image_bytes = dl_resp.read()
                        
                        if len(image_bytes) < 100:
                            logger.error(f"Downloaded invalid image bytes: {image_bytes}")
                            progress_callback(0, "Downloaded file too small to be valid image.")
                            return False
                            
                        with open(save_path, "wb") as f:
                            f.write(image_bytes)
                            
                        # Try to convert webp to png
                        try:
                            from PIL import Image as PILImage
                            png_path = save_path.replace(".webp", ".png")
                            PILImage.open(save_path).save(png_path, "PNG")
                            os.remove(save_path)
                            save_path = png_path
                        except Exception as e:
                            logger.warning(f"Failed to convert webp to png: {e}")
                            
                        logger.info(f"AI Horde image saved to {save_path}")
                        progress_callback(100, f"Downloaded: {os.path.basename(save_path)}")
                        return True
                    else:
                        progress_callback(100, "Done (No auto-download config)")
                        return True
                        
                progress_callback(50 + min(25, int(i / max_polls * 25)), f"Polling... Wait: {wait_time}s, Queue: {queue_pos}")
                time.sleep(10)
                
            progress_callback(0, "Timed out waiting for Horde generation.")
            return False

        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8', errors='ignore')
            logger.error(f"AI Horde HTTP Error {e.code}: {err_body}")
            print(f"AI Horde HTTP Error {e.code}: {err_body}")
            progress_callback(0, f"HTTP Error {e.code}: {err_body}")
            return False
        except Exception as e:
            logger.error(f"AI Horde Request Error: {e}")
            progress_callback(0, f"Request Error: {e}")
            return False

    def shutdown(self):
        pass
