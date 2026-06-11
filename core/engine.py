import threading
import time
from queue import Queue
from core.web_automation import WebAutomationRunner
from core.comfy_client import ComfyUIClient
from core.custom_api_client import CustomAPIClient
from utils.logger import get_logger

logger = get_logger()

class AutomationEngine:
    def __init__(self, callbacks):
        self.callbacks = callbacks
        self.thread = None
        self.queue = Queue()
        
        # State flags
        self.is_running = False
        self.is_paused = False
        self.stop_requested = False
        
        self.current_generator_config = None
        self.downloads_path = ""
        self.auto_name = True
        self.auto_download = True
        self.aspect_ratio = "1:1"

    def set_generator_config(self, config):
        self.current_generator_config = config
        
    def set_download_settings(self, folder, auto_name, auto_download):
        self.downloads_path = folder
        self.auto_name = auto_name
        self.auto_download = auto_download

    def set_aspect_ratio(self, aspect_ratio):
        self.aspect_ratio = aspect_ratio

    def add_prompts(self, prompts):
        for p in prompts:
            if p.strip():
                self.queue.put(p.strip())
        self.callbacks.on_queue_update(self.queue.qsize())

    def clear_queue(self):
        with self.queue.mutex:
            self.queue.queue.clear()
        self.callbacks.on_queue_update(0)

    def start(self):
        if self.is_running and not self.is_paused:
            return
        if self.is_paused:
            self.is_paused = False
            self.callbacks.on_status_change("Running")
            return
            
        self.is_running = True
        self.is_paused = False
        self.stop_requested = False
        self.thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.thread.start()
        self.callbacks.on_status_change("Running")

    def pause(self):
        if self.is_running:
            self.is_paused = True
            self.callbacks.on_status_change("Paused")

    def stop(self):
        self.stop_requested = True
        self.is_running = False
        self.is_paused = False
        self.callbacks.on_status_change("Stopped")

    def _worker_loop(self):
        runner = None
        if self.current_generator_config:
            gen_type = self.current_generator_config.get("type")
            if gen_type == "web":
                runner = WebAutomationRunner(self.current_generator_config, self.downloads_path)
            elif gen_type in ("comfyui", "comfyui_provider"):
                runner = ComfyUIClient(self.current_generator_config, self.downloads_path)
            elif gen_type == "custom_api":
                runner = CustomAPIClient(self.current_generator_config, self.downloads_path)
        
        try:
            if runner and hasattr(runner, 'startup'):
                try:
                    runner.startup(self.callbacks.on_progress_update)
                except Exception as e:
                    logger.error(f"Startup Error: {str(e)}")
                    self.callbacks.on_progress_update(0, f"Startup Error: {str(e)}")
                    self.callbacks.on_status_change("Error")
                    self.stop_requested = True
                    return

            while self.is_running and not self.stop_requested:
                if self.is_paused:
                    time.sleep(0.5)
                    continue

                if self.queue.empty():
                    self.stop()
                    break

                prompt = self.queue.get()
                self.callbacks.on_progress_update(0, "Generating...")
                
                try:
                    if runner:
                        success = runner.generate_and_download(
                            prompt,
                            self.auto_name,
                            self.auto_download,
                            self.callbacks.on_progress_update,
                            negative_prompt=None,
                            aspect_ratio=self.aspect_ratio,
                            should_stop=lambda: self.stop_requested
                        )
                        if success:
                            self.callbacks.on_prompt_completed()
                        else:
                            self.callbacks.on_prompt_failed()
                    else:
                        time.sleep(2)
                        self.callbacks.on_prompt_completed()
                except Exception as e:
                    logger.error(f"Error processing prompt: {e}")
                    self.callbacks.on_prompt_failed()
                
                self.callbacks.on_queue_update(self.queue.qsize())
                self.queue.task_done()
                self.callbacks.on_progress_update(100, "Ready")

        finally:
            if runner and hasattr(runner, 'shutdown'):
                runner.shutdown()
            self.is_running = False
            if not self.stop_requested and self.queue.empty():
                self.callbacks.on_status_change("Finished")
