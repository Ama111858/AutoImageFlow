import sys
import os

# Add core to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.horde_client import HordeClient

def callback(percent, text):
    print(f"[{percent}%] {text}")

def run_test():
    import json
    settings_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "settings.json")
    api_key = "0000000000"
    if os.path.exists(settings_path):
        with open(settings_path, 'r') as f:
            data = json.load(f)
            api_key = data.get("custom_api", {}).get("api_key", "0000000000")

    config = {
        "api_key": api_key,
        "model_selection": "DreamShaper"
    }
    
    download_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_outputs")
    os.makedirs(download_folder, exist_ok=True)
    
    client = HordeClient(config, download_folder)
    
    prompt = "A red apple on a wooden table, realistic photo"
    print(f"Starting test with prompt: {prompt}")
    
    success = client.generate_and_download(
        prompt=prompt,
        auto_name=True,
        auto_download=True,
        progress_callback=callback
    )
    
    if success:
        print("Success! A valid image should be in the test_outputs folder.")
    else:
        print("Failed.")

if __name__ == "__main__":
    run_test()
