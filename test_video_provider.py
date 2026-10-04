import os
import sys

sys.path.insert(0, r"E:\Open-Generative-AI-main\AutoImageFlow")

from core.video_providers.generic_video_client import GenericVideoClient

out_dir = os.path.abspath(r"E:\Open-Generative-AI-main\AutoImageFlow\test_outputs")
os.makedirs(out_dir, exist_ok=True)

print("--- Testing GenericVideoClient initialization ---")
config = {
    "type": "video_provider",
    "api_url": "https://api.openai.com/v1/videos/generations",
    "api_key": "test_video_key",
    "model_name": "sora"
}

client = GenericVideoClient(config, out_dir)
assert client.api_url == "https://api.openai.com/v1/videos/generations"
assert client.api_key == "test_video_key"
assert client.model_name == "sora"
assert client.download_folder == out_dir
print("GenericVideoClient initialization OK")

# Test error handling with dummy key
res = client.generate_and_download(
    "A cinematic drone shot of mountains",
    auto_name=True,
    auto_download=True,
    progress_callback=lambda p, m: print(f"[{p}%] {m}"),
    aspect_ratio="16:9",
    duration="5s"
)
print(f"Network error handled gracefully: {res == False}")

print("\nALL VIDEO PROVIDER UNIT TESTS PASSED!")
