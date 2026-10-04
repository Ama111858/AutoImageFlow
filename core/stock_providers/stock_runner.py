import os
from core.stock_providers.pexels_client import PexelsClient
from core.stock_providers.pixabay_client import PixabayClient
from utils.logger import get_logger

logger = get_logger()

class StockMediaRunner:
    """
    Adapter that allows AutomationEngine to process stock media queues (Pexels / Pixabay)
    using the standard runner interface.
    """

    def __init__(self, config, download_folder):
        self.config = config
        self.download_folder = download_folder
        self.provider = self.config.get("provider", "pexels").lower()
        self.media_type = self.config.get("media_type", "photos").lower()
        self.count = int(self.config.get("count", 2))
        self.orientation = self.config.get("orientation", None)
        api_key = self.config.get("api_key", "").strip()

        if self.provider == "pixabay":
            self.client = PixabayClient(api_key, download_folder)
        else:
            self.client = PexelsClient(api_key, download_folder)

    def startup(self, progress_callback=None):
        if progress_callback:
            progress_callback(10, f"Stock Provider ({self.provider.title()}) Ready")
        logger.info(f"StockMediaRunner started with provider={self.provider}, media_type={self.media_type}")

    def generate_and_download(self, prompt, auto_name, auto_download, progress_callback, **kwargs):
        should_stop = kwargs.get("should_stop", lambda: False)
        orientation = self.orientation
        if not orientation and "aspect_ratio" in kwargs:
            ar = str(kwargs.get("aspect_ratio", "")).strip().lower()
            if any(x in ar for x in ("9:16", "3:4", "short", "vertical")):
                orientation = "vertical"
            elif ar:
                orientation = "horizontal"

        if self.media_type == "both":
            result = self.client.search_and_download(
                query=prompt,
                media_type="videos",
                count=self.count,
                orientation=orientation,
                progress_callback=progress_callback,
                should_stop=should_stop
            )
            downloaded = result.get("downloaded_files", [])
            if not downloaded:
                result = self.client.search_and_download(
                    query=prompt,
                    media_type="photos",
                    count=self.count,
                    orientation=orientation,
                    progress_callback=progress_callback,
                    should_stop=should_stop
                )
                downloaded = result.get("downloaded_files", [])
        else:
            result = self.client.search_and_download(
                query=prompt,
                media_type=self.media_type,
                count=self.count,
                orientation=orientation,
                progress_callback=progress_callback,
                should_stop=should_stop
            )
            downloaded = result.get("downloaded_files", [])
        return result.get("success", False) and len(downloaded) > 0

    def shutdown(self):
        logger.info("StockMediaRunner shutdown.")
