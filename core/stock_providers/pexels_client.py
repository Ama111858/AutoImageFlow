import os
import re
import uuid
import json
import urllib.request
import urllib.parse
import urllib.error
from utils.logger import get_logger

logger = get_logger()

class PexelsClient:
    """
    Client for Pexels Free Stock Media API (Photos and Videos).
    """

    PHOTO_API = "https://api.pexels.com/v1/search"
    VIDEO_API = "https://api.pexels.com/videos/search"

    def __init__(self, api_key, download_folder):
        self.api_key = api_key.strip() if api_key else ""
        self.download_folder = download_folder

    def search_and_download(self, query, media_type="photos", count=3, orientation=None, progress_callback=None, should_stop=lambda: False):
        """
        Search Pexels for media and download matching files into download_folder.
        media_type: 'photos' or 'videos'
        """
        if not self.api_key:
            err = "Pexels Error: API key is not configured."
            logger.error(err)
            if progress_callback:
                progress_callback(0, err)
            return {"success": False, "error": err, "downloaded_files": []}

        if progress_callback:
            progress_callback(10, f"Searching Pexels for '{query}' ({media_type})...")

        headers = {
            "Authorization": self.api_key,
            "User-Agent": "AutoImageFlow-StockClient/1.0"
        }

        params = {
            "query": query,
            "per_page": min(max(int(count), 1), 20)
        }
        if orientation and orientation in ("landscape", "portrait", "square"):
            params["orientation"] = orientation

        endpoint = self.VIDEO_API if media_type == "videos" else self.PHOTO_API
        url = f"{endpoint}?{urllib.parse.urlencode(params)}"

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            items = data.get("videos" if media_type == "videos" else "photos", [])
            if not items:
                msg = f"No {media_type} found on Pexels for '{query}'"
                logger.info(msg)
                if progress_callback:
                    progress_callback(100, msg)
                return {"success": True, "error": None, "downloaded_files": []}

            logger.info(f"Found {len(items)} items on Pexels for '{query}'. Downloading...")
            os.makedirs(self.download_folder, exist_ok=True)
            downloaded = []

            safe_q = re.sub(r'[\\/*?:"<>|\n\r\t]', "", query[:25]).replace(" ", "_")

            for i, item in enumerate(items[:count]):
                if should_stop():
                    logger.info("Stock download stopped by user.")
                    break

                pct = 20 + int(((i + 1) / len(items[:count])) * 75)
                if progress_callback:
                    progress_callback(pct, f"Downloading {media_type[:-1]} {i+1} of {len(items[:count])}...")

                # Extract download URL
                dl_url = None
                ext = ".jpg" if media_type == "photos" else ".mp4"

                if media_type == "photos":
                    src = item.get("src", {})
                    dl_url = src.get("original") or src.get("large2x") or src.get("large")
                else:
                    video_files = item.get("video_files", [])
                    # Pick highest resolution or HD mp4
                    sorted_files = sorted(
                        [vf for vf in video_files if vf.get("file_type") == "video/mp4"],
                        key=lambda x: (x.get("width", 0) or 0),
                        reverse=True
                    )
                    if sorted_files:
                        dl_url = sorted_files[0].get("link")

                if not dl_url:
                    continue

                filename = f"pexels_{safe_q}_{str(uuid.uuid4())[:6]}{ext}"
                save_path = os.path.join(self.download_folder, filename)

                try:
                    dl_req = urllib.request.Request(dl_url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(dl_req, timeout=40) as dl_resp:
                        with open(save_path, "wb") as f_out:
                            while True:
                                chunk = dl_resp.read(65536)
                                if not chunk:
                                    break
                                f_out.write(chunk)

                    if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
                        downloaded.append(save_path)
                        logger.info(f"Saved: {save_path} ({os.path.getsize(save_path)} bytes)")
                except Exception as de:
                    logger.error(f"Failed downloading item {i+1}: {de}")

            if progress_callback:
                progress_callback(100, f"Downloaded {len(downloaded)} items from Pexels")

            return {"success": True, "error": None, "downloaded_files": downloaded}

        except urllib.error.HTTPError as he:
            err_msg = f"Pexels HTTP {he.code}: {he.reason}"
            logger.error(err_msg)
            if progress_callback:
                progress_callback(0, err_msg)
            return {"success": False, "error": err_msg, "downloaded_files": []}
        except Exception as e:
            err_msg = f"Pexels error: {e}"
            logger.error(err_msg)
            if progress_callback:
                progress_callback(0, err_msg)
            return {"success": False, "error": err_msg, "downloaded_files": []}
