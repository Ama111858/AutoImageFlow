import json
import os

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "settings.json")

DEFAULT_SETTINGS = {
    "active_provider": "Built-in Provider",
    "comfyui": {
        "server_url": "http://127.0.0.1:8188",
        "workflow_path": ""
    },
    "custom_api": {
        "api_url": "https://api.openai.com/v1/images/generations",
        "api_key": "",
        "model_name": "dall-e-3"
    },
    "video_provider": {
        "api_url": "https://api.openai.com/v1/videos/generations",
        "api_key": "",
        "model_name": "sora",
        "aspect_ratio": "16:9",
        "duration": "5s"
    },
    "stock_providers": {
        "pexels_api_key": "",
        "pixabay_api_key": ""
    }
}

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return DEFAULT_SETTINGS.copy()
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Merge with defaults in case of missing keys
            settings = DEFAULT_SETTINGS.copy()
            settings.update(data)
            return settings
    except Exception as e:
        logger.error(f"Error loading settings: {e}")
        return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    try:
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
        return True
    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        return False
