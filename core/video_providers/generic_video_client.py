import os
import time
import uuid
import re
import json
import urllib.request
import urllib.error
from core.video_providers.base import BaseVideoProvider
from utils.logger import get_logger

logger = get_logger()

class GenericVideoClient(BaseVideoProvider):
    """
    Extensible REST-based AI Video Generation Client.
    Supports asynchronous generation APIs (Runway, Luma, Replicate, Fal, OpenAI, or custom endpoints).
    """

    def __init__(self, config, download_folder):
        super().__init__(config, download_folder)
        self.api_url = self.config.get("api_url", "").strip()
        self.api_key = self.config.get("api_key", "").strip()
        self.model_name = self.config.get("model_name", "generic-video").strip()
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "AutoImageFlow-VideoClient/1.0"
        }
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

    def startup(self, progress_callback=None):
        if progress_callback:
            progress_callback(10, "Video Provider initialized")
        logger.info(f"GenericVideoClient startup: {self.api_url} (model: {self.model_name})")

    def generate_and_download(self, prompt, auto_name, auto_download, progress_callback, **kwargs):
        aspect_ratio = kwargs.get("aspect_ratio", "16:9")
        duration = kwargs.get("duration", "5s")
        should_stop = kwargs.get("should_stop", lambda: False)

        if not self.api_url:
            logger.error("Video Generation Error: API URL is not configured.")
            if progress_callback:
                progress_callback(0, "Error: API URL is not configured")
            return False

        if progress_callback:
            progress_callback(15, "Submitting video generation request...")

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "duration": duration
        }

        try:
            req = urllib.request.Request(
                self.api_url,
                data=json.dumps(payload).encode("utf-8"),
                headers=self.headers,
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=30) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))

            logger.info(f"Video generation task submitted: {resp_data}")

            # Check if video URL was returned immediately
            video_url = None
            task_id = resp_data.get("id") or resp_data.get("task_id")

            # Direct video URL in response
            if "video_url" in resp_data:
                video_url = resp_data["video_url"]
            elif "output" in resp_data and isinstance(resp_data["output"], str):
                video_url = resp_data["output"]
            elif "data" in resp_data and isinstance(resp_data["data"], list) and len(resp_data["data"]) > 0:
                video_url = resp_data["data"][0].get("url")

            # If task ID returned, poll for completion
            if not video_url and task_id:
                poll_url = f"{self.api_url.rstrip('/')}/{task_id}"
                max_polls = 120  # up to 10 minutes (5s intervals)
                
                for poll_i in range(max_polls):
                    if should_stop():
                        logger.info("Video generation cancelled by user.")
                        return False

                    time.sleep(5)
                    pct = min(20 + int((poll_i / max_polls) * 60), 80)
                    if progress_callback:
                        progress_callback(pct, f"Generating video... ({poll_i * 5}s)")

                    try:
                        poll_req = urllib.request.Request(poll_url, headers=self.headers, method="GET")
                        with urllib.request.urlopen(poll_req, timeout=20) as poll_resp:
                            poll_data = json.loads(poll_resp.read().decode("utf-8"))

                        status = poll_data.get("status", "").lower()
                        if status in ("succeeded", "completed", "done", "success"):
                            video_url = (
                                poll_data.get("video_url")
                                or poll_data.get("output")
                                or (poll_data.get("output", [None])[0] if isinstance(poll_data.get("output"), list) else None)
                                or (poll_data.get("data", [{}])[0].get("url") if isinstance(poll_data.get("data"), list) else None)
                            )
                            break
                        elif status in ("failed", "error", "canceled"):
                            logger.error(f"Video task failed: {poll_data.get('error', 'Unknown error')}")
                            if progress_callback:
                                progress_callback(0, f"Task Failed: {poll_data.get('error', 'Unknown error')}")
                            return False
                    except Exception as pe:
                        logger.warning(f"Error polling video status: {pe}")

            if not video_url:
                logger.error("No video URL found in API response.")
                if progress_callback:
                    progress_callback(0, "Error: No video URL received")
                return False

            if not auto_download:
                if progress_callback:
                    progress_callback(100, "Done (Download disabled)")
                return True

            # Download Video
            if progress_callback:
                progress_callback(85, "Downloading generated video...")

            if auto_name:
                safe_prompt = re.sub(r'[\\/*?:"<>|\n\r\t]', "", prompt[:30]).replace(" ", "_")
                filename = f"vid_{str(uuid.uuid4())[:6]}_{safe_prompt}.mp4"
            else:
                filename = f"vid_{str(uuid.uuid4())[:6]}.mp4"

            save_path = os.path.join(self.download_folder, filename)
            os.makedirs(self.download_folder, exist_ok=True)

            logger.info(f"Downloading video from {video_url} to {save_path}")
            dl_req = urllib.request.Request(video_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(dl_req, timeout=60) as dl_resp:
                with open(save_path, "wb") as out_f:
                    while True:
                        chunk = dl_resp.read(65536)
                        if not chunk:
                            break
                        out_f.write(chunk)

            if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
                logger.info(f"Video successfully saved: {save_path} ({os.path.getsize(save_path)} bytes)")
                if progress_callback:
                    progress_callback(100, "Video saved successfully")
                return True
            else:
                logger.error("Video download produced empty file.")
                if progress_callback:
                    progress_callback(0, "Download failed")
                return False

        except urllib.error.HTTPError as he:
            err_body = he.read().decode("utf-8", errors="replace")
            logger.error(f"HTTP Error {he.code} during video generation: {err_body}")
            if progress_callback:
                progress_callback(0, f"HTTP Error {he.code}")
            return False
        except Exception as e:
            logger.error(f"Video Generation Error: {e}")
            if progress_callback:
                progress_callback(0, f"Error: {e}")
            return False

    def shutdown(self):
        logger.info("GenericVideoClient shutdown.")
