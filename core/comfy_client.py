import urllib.request
import urllib.parse
import json
import time
import os
import uuid
import shutil
import webbrowser
import random
from utils.logger import get_logger

logger = get_logger()

class ComfyUIClient:
    _browser_opened = False

    def __init__(self, config, download_folder):
        self.config = config
        self.url = self.config["url"]
        self.download_folder = download_folder

    def startup(self, progress_callback=None):
        if progress_callback:
            progress_callback(10, "Checking ComfyUI connection...")

        def open_visible_browser(url):
            if os.environ.get("AUTOIMAGEFLOW_NO_BROWSER") == "1" or ComfyUIClient._browser_opened:
                return
            ComfyUIClient._browser_opened = True
            try:
                os.startfile(url)
            except Exception:
                webbrowser.open(url)

        def check_port(port=8188):
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1.0)
                return s.connect_ex(('127.0.0.1', port)) == 0

        if check_port(8188):
            try:
                req = urllib.request.Request(f"{self.url.rstrip('/')}/system_stats")
                with urllib.request.urlopen(req, timeout=3) as resp:
                    if resp.status == 200:
                        if progress_callback:
                            progress_callback(20, "ComfyUI Connected")
                        if not ComfyUIClient._browser_opened and os.environ.get("AUTOIMAGEFLOW_NO_BROWSER") != "1":
                            logger.info("Auto-opening ComfyUI in browser")
                            open_visible_browser(self.url)
                        return
            except Exception:
                pass

        # If not reachable, auto-launch ComfyUI using existing bat
        if progress_callback:
            progress_callback(15, "Starting ComfyUI server...")
        logger.info("ComfyUI not running, attempting auto-launch...")

        base_dir = r"E:\ComfyUi\ComfyUI_windows_portable"
        cpu_bat = os.path.join(base_dir, "run_cpu.bat")
        gpu_bat = os.path.join(base_dir, "run_nvidia_gpu.bat")
        bat_to_run = cpu_bat
        try:
            import torch
            if torch.cuda.is_available() and torch.cuda.device_count() > 0:
                if os.path.exists(gpu_bat):
                    bat_to_run = gpu_bat
        except Exception:
            pass

        if not os.path.exists(bat_to_run):
            if os.path.exists(gpu_bat):
                bat_to_run = gpu_bat
            elif os.path.exists(cpu_bat):
                bat_to_run = cpu_bat
            else:
                raise Exception(f"ComfyUI startup script not found in {base_dir}")

        import subprocess
        subprocess.Popen(f'"{bat_to_run}"', cwd=base_dir, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)

        # Poll for readiness: wait until check_port PASS and /system_stats responds
        start_t = time.time()
        connected = False
        while time.time() - start_t < 60:
            if check_port(8188):
                try:
                    req = urllib.request.Request(f"{self.url.rstrip('/')}/system_stats")
                    with urllib.request.urlopen(req, timeout=2) as resp:
                        if resp.status == 200:
                            connected = True
                            break
                except Exception:
                    pass
            time.sleep(2)

        if not connected:
            raise Exception("Timed out waiting for ComfyUI to start")

        logger.info("Ready check PASS: opening ComfyUI in browser")
        open_visible_browser(self.url)

        if progress_callback:
            progress_callback(20, "ComfyUI Connected")

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

        selected_model = self.config.get("model_selection", "Realistic Vision")
        
        # Map common names to checkpoint files, or use the provided name directly if it looks like a filename
        target_ckpt = selected_model
        if selected_model == "Realistic Vision":
            target_ckpt = "realisticV51_realisticv15BETA.safetensors"
        elif selected_model == "DreamShaper":
            target_ckpt = "dreamshaper_8.safetensors"
        elif selected_model.lower() == "sdxl":
            target_ckpt = "sd_xl_base_1.0.safetensors"
        elif selected_model.lower() == "sd15":
            target_ckpt = "v1-5-pruned-emaonly.safetensors"
        elif not selected_model.endswith(".safetensors") and not selected_model.endswith(".ckpt"):
            target_ckpt = f"{selected_model}.safetensors"

        # Query ComfyUI for actual installed checkpoints to ensure validation always succeeds
        available_ckpts = []
        try:
            req_info = urllib.request.Request(f"{self.url}/object_info/CheckpointLoaderSimple")
            with urllib.request.urlopen(req_info, timeout=5) as resp_info:
                if resp_info.status == 200:
                    info_data = json.loads(resp_info.read().decode('utf-8'))
                    available_ckpts = info_data.get("CheckpointLoaderSimple", {}).get("input", {}).get("required", {}).get("ckpt_name", [[]])[0]
        except Exception as e:
            logger.warning(f"Could not query ComfyUI checkpoints from {self.url}: {e}")

        resolved_ckpt = target_ckpt
        if available_ckpts:
            if target_ckpt in available_ckpts:
                resolved_ckpt = target_ckpt
            else:
                # Try case-insensitive or substring matching
                matched = None
                for c in available_ckpts:
                    if target_ckpt.lower() in c.lower() or c.lower() in target_ckpt.lower():
                        matched = c
                        break
                # Fallback: pick the first genuine image checkpoint (skip motion modules and VAE files)
                if not matched:
                    valid_ckpts = [c for c in available_ckpts if not c.startswith("mm_") and "vae" not in c.lower()]
                    matched = valid_ckpts[0] if valid_ckpts else available_ckpts[0]
                
                logger.info(f"Checkpoint '{target_ckpt}' not in ComfyUI. Auto-resolved to installed checkpoint '{matched}'")
                resolved_ckpt = matched

        for node_id, node_info in workflow.items():
            if node_info.get("class_type") == "CheckpointLoaderSimple":
                if "inputs" in node_info:
                    node_info["inputs"]["ckpt_name"] = resolved_ckpt
                    logger.info(f"Set Checkpoint to {resolved_ckpt}")
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
            
        # Initial image generation resolution = 512 x 512 (Short/Long resolution not implemented yet as per requirement)
        target_w, target_h = 512, 512

        latent_injected = False
        for node_id, node_info in workflow.items():
            if node_info.get("class_type") == "EmptyLatentImage" and "inputs" in node_info:
                node_info["inputs"]["width"] = target_w
                node_info["inputs"]["height"] = target_h
                latent_injected = True
                logger.info(f"Set EmptyLatentImage initial resolution to {target_w}x{target_h} at Node {node_id}")
                break

        if not latent_injected and "5" in workflow and "inputs" in workflow["5"]:
            workflow["5"]["inputs"]["width"] = target_w
            workflow["5"]["inputs"]["height"] = target_h
            logger.info(f"Set EmptyLatentImage initial resolution to {target_w}x{target_h} at fallback Node 5")

        # Randomize seed for KSampler to guarantee a fresh generation for each prompt
        for node_id, node_info in workflow.items():
            if node_info.get("class_type") in ("KSampler", "KSamplerAdvanced") and "inputs" in node_info:
                node_info["inputs"]["seed"] = random.randint(1, 10**14)
                break

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
