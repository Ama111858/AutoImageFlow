import sys
import os
import time

sys.path.insert(0, r"E:\Open-Generative-AI-main\AutoImageFlow")

from core.web_automation import WebAutomationRunner
from utils.config_manager import load_generators

generators = load_generators()
print(f"Loaded {len(generators)} generators: {[g.get('name') for g in generators]}")

config = generators[0]
print(f"Using generator: {config.get('name')} -> {config.get('url')}")

out_dir = os.path.abspath(r"E:\Open-Generative-AI-main\AutoImageFlow\test_outputs")
os.makedirs(out_dir, exist_ok=True)

runner = WebAutomationRunner(config, out_dir)

def progress_cb(pct, msg):
    print(f"PROGRESS [{pct}%]: {msg}")

try:
    print("Starting runner.startup()...")
    runner.startup(progress_cb)
    print("Startup complete! Generating images...")
    
    prompts = [
        "A futuristic cyberpunk city with neon lights and flying cars in rain",
        "An astronaut riding a horse on Mars, photorealistic, cinematic"
    ]
    for idx, p in enumerate(prompts):
        print(f"\n--- Generating image {idx+1}/{len(prompts)}: '{p}' ---")
        success = runner.generate_and_download(
            prompt=p,
            auto_name=True,
            auto_download=True,
            progress_callback=progress_cb,
            aspect_ratio="1:1"
        )
        print(f"generate_and_download {idx+1} result: {success}")
    
    # Check outputs
    files = os.listdir(out_dir)
    print(f"\nFinal files in {out_dir}: {files}")
finally:
    print("Shutting down runner...")
    runner.shutdown()
