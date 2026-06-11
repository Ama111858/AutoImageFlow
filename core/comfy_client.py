import urllib.request
import urllib.parse
import json
import time
import os
import uuid
import shutil
import webbrowser
from utils.logger import get_logger

logger = get_logger()

class ComfyUIClient:
    def __init__(self, config, download_folder):
        self.config = config
        self.url = self.config["url"]
        self.download_folder = download_folder

    def startup(self, progress_callback=None):
        if progress_callback:
            progress_callback(10, "Checking ComfyUI connection...")
        try:
            req = urllib.request.Request(f"{self.url.rstrip('/')}/system_stats")
            urllib.request.urlopen(req, timeout=5)
            if progress_callback:
                progress_callback(20, "ComfyUI Connected")
            
            logger.info("Auto-opening ComfyUI in browser")
            webbrowser.open(self.url)
            
        except Exception as e:
            raise Exception(f"Connection Failed: {e}")

    def get_history(self, prompt_id):
        req = urllib.request.Request(f"{self.url}/history/{prompt_id}")
        try:
            response = urllib.request.urlopen(req)
            return json.loads(response.read())
        except Exception:
            return None

    def get_image(self, filename, subfolder, folder_type):
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url_values = urllib.parse.urlencode(data)
        req = urllib.request.Request(f"{self.url}/view?{url_values}")
        try:
            response = urllib.request.urlopen(req)
            return response.read()
        except Exception:
            return None

    def generate_and_download(self, prompt_text, auto_name, auto_download, progress_callback, negative_prompt=None, aspect_ratio="1:1", should_stop=None, **kwargs):
        logger.info(f"Prompt Captured: '{prompt_text}'")
        self.url = self.url.rstrip("/")
        # Look for workflow_api.json in the parent directory, or use config provided path
        workflow_path = self.config.get("workflow_path", "").strip()
        if not workflow_path or not os.path.exists(workflow_path):
            import sys
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
                # In PyInstaller, the bundled files are in _internal (or _MEIPASS)
                internal_dir = getattr(sys, '_MEIPASS', os.path.dirname(__file__))
            else:
                base_dir = os.path.dirname(os.path.dirname(__file__))
                internal_dir = base_dir
            
            # Try next to the executable first
            workflow_path = os.path.join(base_dir, "workflow_api.json")
            
            # Fallback to the bundled default workflow
            if not os.path.exists(workflow_path):
                workflow_path = os.path.join(internal_dir, "config", "workflow_api.json")
            
        if not os.path.exists(workflow_path):
            logger.error(f"Missing {workflow_path}")
            if progress_callback:
                progress_callback(0, f"Error: {workflow_path} not found.")
            return False
            
        with open(workflow_path, "r", encoding="utf-8") as f:
            workflow = json.load(f)

        selected_model = self.config.get("model_selection", "DreamShaper")
        target_ckpt = "dreamshaper_8.safetensors"
        if selected_model == "Realistic Vision":
            target_ckpt = "realisticV51_realisticv15BETA.safetensors"
            
        for node_id, node_info in workflow.items():
            if node_info.get("class_type") == "CheckpointLoaderSimple":
                if "inputs" in node_info:
                    node_info["inputs"]["ckpt_name"] = target_ckpt
                    logger.info(f"Set Checkpoint to {target_ckpt}")
                    break

        prompt_injected = False
        
        # Try to inject into the standard node 6 first
        if "6" in workflow and "inputs" in workflow["6"] and "text" in workflow["6"]["inputs"]:
            workflow["6"]["inputs"]["text"] = prompt_text
            prompt_injected = True
            logger.info("Prompt Injected at Node 6")
        else:
            # Fallback to the first CLIPTextEncode
            for node_id, node_info in workflow.items():
                if node_info.get("class_type") == "CLIPTextEncode" and "inputs" in node_info and "text" in node_info["inputs"]:
                    node_info["inputs"]["text"] = prompt_text
                    prompt_injected = True
                    logger.info(f"Prompt Injected at fallback Node {node_id}")
                    break
        
        if not prompt_injected:
            logger.warning("Could not find a valid CLIPTextEncode node for the prompt.")
            
        logger.info("Workflow Updated")
        
        p = {"prompt": workflow}
        data = json.dumps(p).encode('utf-8')
        logger.info(f"Payload Sent. Target URL: {self.url}/prompt")
        req = urllib.request.Request(f"{self.url}/prompt", data=data)
        
        try:
            progress_callback(20, "Queuing prompt...")
            response = urllib.request.urlopen(req)
            response_data = response.read()
            logger.info(f"Queue Submitted. Server Response: {response_data}")
            
            result = json.loads(response_data)
            prompt_id = result.get("prompt_id")
            
            if not prompt_id:
                logger.error("No prompt_id received from ComfyUI.")
                return False
                
            logger.info(f"Generation Started. Prompt ID: {prompt_id}")
                
            progress_callback(40, "Waiting for generation...")
            
            # Poll history
            history = None
            while True:
                if should_stop and should_stop():
                    progress_callback(100, "Stopped")
                    return False
                history = self.get_history(prompt_id)
                if history and prompt_id in history:
                    break
                time.sleep(2)
            
            progress_callback(80, "Generation complete. Downloading...")
            if auto_download:
                history_data = history[prompt_id]
                for node_id in history_data.get('outputs', {}):
                    node_output = history_data['outputs'][node_id]
                    if 'images' in node_output:
                        for image in node_output['images']:
                            image_data = self.get_image(image['filename'], image['subfolder'], image['type'])
                            if image_data:
                                if auto_name:
                                    safe_prompt = prompt_text[:15].replace(' ', '_').replace(':', '')
                                    filename = f"{str(uuid.uuid4())[:8]}_{safe_prompt}.png"
                                else:
                                    filename = image['filename']
                                save_path = os.path.join(self.download_folder, filename)
                                with open(save_path, "wb") as f:
                                    f.write(image_data)
                                progress_callback(100, f"Downloaded: {filename}")
            else:
                progress_callback(100, "Done (No auto-download config)")
            return True
            
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8', errors='ignore')
            logger.error(f"ComfyUI HTTP Error {e.code}: {err_body}")
            if progress_callback:
                progress_callback(0, f"HTTP Error {e.code}: {err_body[:50]}")
            return False
        except Exception as e:
            logger.error(f"ComfyUI Error: {e}")
            if progress_callback:
                progress_callback(0, f"Error: {e}")
            return False

    def shutdown(self):
        pass
