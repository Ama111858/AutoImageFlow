import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "generators.json")

def load_generators():
    if not os.path.exists(CONFIG_PATH):
        return []
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            return data.get("generators", [])
        except json.JSONDecodeError:
            return []

def save_generators(generators):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump({"generators": generators}, f, indent=4)
