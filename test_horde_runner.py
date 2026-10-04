import sys
import os

sys.path.insert(0, r"E:\Open-Generative-AI-main\AutoImageFlow")

from core.horde_client import HordeClient

out_dir = os.path.abspath(r"E:\Open-Generative-AI-main\AutoImageFlow\test_outputs")
os.makedirs(out_dir, exist_ok=True)

config = {
    "api_key": "0000000000",
    "model_selection": "DreamShaper"
}

client = HordeClient(config, out_dir)

def progress_cb(pct, msg):
    print(f"HORDE [{pct}%]: {msg}", flush=True)

print("Starting HordeClient test...")
success = client.generate_and_download(
    prompt="a small cute wooden cottage in forest, vibrant, sunny day",
    auto_name=True,
    auto_download=True,
    progress_callback=progress_cb,
    aspect_ratio="1:1"
)
print(f"Success: {success}")
print(f"Files: {os.listdir(out_dir)}")
