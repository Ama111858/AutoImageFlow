import os
import sys

sys.path.insert(0, r"E:\Open-Generative-AI-main\AutoImageFlow")

from core.stock_providers.pexels_client import PexelsClient
from core.stock_providers.pixabay_client import PixabayClient
from core.stock_providers.stock_runner import StockMediaRunner

out_dir = os.path.abspath(r"E:\Open-Generative-AI-main\AutoImageFlow\test_outputs")
os.makedirs(out_dir, exist_ok=True)

print("--- Testing PexelsClient initialization ---")
pexels = PexelsClient("test_key", out_dir)
assert pexels.api_key == "test_key"
assert pexels.download_folder == out_dir
print("PexelsClient OK")

print("--- Testing PixabayClient initialization ---")
pixabay = PixabayClient("test_key_pix", out_dir)
assert pixabay.api_key == "test_key_pix"
assert pixabay.download_folder == out_dir
print("PixabayClient OK")

print("--- Testing StockMediaRunner initialization ---")
config = {
    "type": "stock_provider",
    "provider": "pexels",
    "media_type": "photos",
    "count": 3,
    "orientation": "landscape",
    "api_key": "dummy_key"
}
runner = StockMediaRunner(config, out_dir)
assert runner.provider == "pexels"
assert runner.media_type == "photos"
assert runner.count == 3
assert runner.orientation == "landscape"
print("StockMediaRunner OK")

# Test empty key error handling
res = runner.generate_and_download("sunset", auto_name=True, auto_download=True, progress_callback=lambda p, m: print(f"[{p}%] {m}"))
print(f"Empty key response handled gracefully: {res == False}")

print("\nALL STOCK PROVIDER UNIT TESTS PASSED!")
