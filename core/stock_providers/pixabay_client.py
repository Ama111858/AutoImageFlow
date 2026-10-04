import os
import re
import uuid
import json
import urllib.request
import urllib.parse
import urllib.error
from utils.logger import get_logger

logger = get_logger()

class PixabayClient:
    """
    Client for Pixabay Free Stock Media API (Photos and Videos).
    """

    PHOTO_API = "https://pixabay.com/api/"
    VIDEO_API = "https://pixabay.com/api/videos/"

    def __init__(self, api_key, download_folder):
        self.api_key = api_key.strip() if api_key else ""
        self.download_folder = download_folder

    def search_and_download(self, query, media_type="photos", count=3, orientation=None, progress_callback=None, should_stop=lambda: False):
        """
        Search Pixabay for media and download matching files into download_folder.
        media_type: 'photos' or 'videos'
        """
        if not self.api_key:
            err = "Pixabay Error: API key is not configured."
            logger.error(err)
            if progress_callback:
                progress_callback(0, err)
            return {"success": False, "error": err, "downloaded_files": []}

        if progress_callback:
            progress_callback(10, f"Searching Pixabay for '{query}' ({media_type})...")

        # Increase per_page when filtering by orientation (Pixabay Video API does not filter orientation server-side)
        fetch_count = min(max(int(count) * 20, 50), 100) if orientation else min(max(int(count), 3), 20)
        params = {
            "key": self.api_key,
            "q": query,
            "per_page": fetch_count,
            "safesearch": "true"
        }

        if media_type == "photos":
            params["image_type"] = "photo"
            if orientation and orientation in ("horizontal", "vertical"):
                params["orientation"] = orientation
            endpoint = self.PHOTO_API
        else:
            endpoint = self.VIDEO_API

        url = f"{endpoint}?{urllib.parse.urlencode(params)}"

        def _get_hit_dims(hit, m_type):
            if m_type == "photos":
                return hit.get("imageWidth", 0), hit.get("imageHeight", 0)
            videos = hit.get("videos", {})
            for res in ("medium", "large", "small", "tiny"):
                if res in videos and videos[res].get("width") and videos[res].get("height"):
                    return videos[res]["width"], videos[res]["height"]
            return 0, 0

        def _matches_orientation(hit, m_type, desired_orientation):
            if not desired_orientation or desired_orientation not in ("horizontal", "vertical"):
                return True
            w, h = _get_hit_dims(hit, m_type)
            if w <= 0 or h <= 0:
                return True
            if desired_orientation == "vertical":
                return h > w
            else:
                return w > h

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AutoImageFlow-StockClient/1.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            raw_hits = data.get("hits", [])
            hits = [h for h in raw_hits if _matches_orientation(h, media_type, orientation)]

            if not hits:
                # Fallback: if query has multiple words, try first 2-3 substantive terms
                words = [w for w in re.split(r'[,;\s]+', query.strip()) if len(w) > 2 and w.lower() not in ("the", "and", "with", "for", "from", "that", "this")]
                if len(words) > 1:
                    fallback_q = " ".join(words[:2])
                    logger.info(f"0 matching {orientation} hits for '{query}'. Trying fallback: '{fallback_q}'")
                    params["q"] = fallback_q
                    fallback_url = f"{endpoint}?{urllib.parse.urlencode(params)}"
                    try:
                        f_req = urllib.request.Request(fallback_url, headers={"User-Agent": "AutoImageFlow-StockClient/1.0"})
                        with urllib.request.urlopen(f_req, timeout=20) as f_resp:
                            f_data = json.loads(f_resp.read().decode("utf-8"))
                        f_raw_hits = f_data.get("hits", [])
                        hits = [h for h in f_raw_hits if _matches_orientation(h, media_type, orientation)]
                    except Exception as fe:
                        logger.warning(f"Fallback query failed: {fe}")

            if not hits and orientation:
                logger.info(f"0 matching {orientation} hits for '{query}'. Trying fallback without orientation constraint...")
                hits = raw_hits or (f_raw_hits if 'f_raw_hits' in locals() else [])

            if not hits:
                msg = f"No {orientation or ''} {media_type} found on Pixabay for '{query}'"
                logger.info(msg)
                if progress_callback:
                    progress_callback(100, msg)
                return {"success": True, "error": None, "downloaded_files": []}

            logger.info(f"Found {len(hits)} matching {orientation or ''} items on Pixabay for '{query}'. Downloading...")
            os.makedirs(self.download_folder, exist_ok=True)
            downloaded = []

            safe_q = re.sub(r'[\\/*?:"<>|\n\r\t]', "", query[:25]).replace(" ", "_")

            for i, hit in enumerate(hits[:count]):
                if should_stop():
                    logger.info("Stock download stopped by user.")
                    break

                pct = 20 + int(((i + 1) / len(hits[:count])) * 75)
                if progress_callback:
                    progress_callback(pct, f"Downloading {media_type[:-1]} {i+1} of {len(hits[:count])}...")

                dl_url = None
                ext = ".jpg" if media_type == "photos" else ".mp4"

                if media_type == "photos":
                    dl_url = hit.get("largeImageURL") or hit.get("fullHDURL") or hit.get("imageURL") or hit.get("webformatURL")
                else:
                    videos = hit.get("videos", {})
                    # Prefer large, medium, then small
                    for res in ("large", "medium", "small", "tiny"):
                        if res in videos and videos[res].get("url"):
                            dl_url = videos[res]["url"]
                            break

                if not dl_url:
                    continue

                filename = f"pixabay_{safe_q}_{str(uuid.uuid4())[:6]}{ext}"
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
                progress_callback(100, f"Downloaded {len(downloaded)} items from Pixabay")

            return {"success": True, "error": None, "downloaded_files": downloaded}

        except urllib.error.HTTPError as he:
            err_msg = f"Pixabay HTTP {he.code}: {he.reason}"
            logger.error(err_msg)
            if progress_callback:
                progress_callback(0, err_msg)
            return {"success": False, "error": err_msg, "downloaded_files": []}
        except Exception as e:
            err_msg = f"Pixabay error: {e}"
            logger.error(err_msg)
            if progress_callback:
                progress_callback(0, err_msg)
            return {"success": False, "error": err_msg, "downloaded_files": []}
