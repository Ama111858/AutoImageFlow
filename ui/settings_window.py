import customtkinter as ctk
import urllib.request
from utils.settings_manager import save_settings
from utils.ui_utils import add_context_menu

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, master, settings, on_save_callback):
        super().__init__(master)
        
        self.title("Settings")
        self.geometry("550x800")
        self.settings = settings
        self.on_save_callback = on_save_callback
        
        self.test_positive_prompt = ""
        self.test_negative_prompt = ""
        
        # Bring window to front
        self.transient(master)
        self.grab_set()

        self._setup_ui()
        self._load_current_settings()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Provider Selection
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        
        ctk.CTkLabel(top_frame, text="Active Provider:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 10))
        
        self.provider_var = ctk.StringVar(value=self.settings.get("active_provider", "Built-in Provider"))
        self.provider_dropdown = ctk.CTkOptionMenu(
            top_frame, 
            variable=self.provider_var,
            values=["Built-in Provider", "ComfyUI", "Custom API", "AI Video Provider", "Stock Media (Pexels/Pixabay)"],
            command=self._on_provider_change
        )
        self.provider_dropdown.pack(side="left", fill="x", expand=True)

        # Dynamic Content Frame
        self.content_frame = ctk.CTkFrame(self, corner_radius=10)
        self.content_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.content_frame.grid_columnconfigure(1, weight=1)

        # Built-in Provider Frame
        self.builtin_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        ctk.CTkLabel(self.builtin_frame, text="Uses the existing generators configuration.\n\nNo additional settings required.", justify="center").pack(pady=50)

        # ComfyUI Frame
        self.comfyui_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.comfyui_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.comfyui_frame, text="Server URL:").grid(row=0, column=0, padx=10, pady=(20, 10), sticky="e")
        self.comfyui_url_entry = ctk.CTkEntry(self.comfyui_frame)
        self.comfyui_url_entry.grid(row=0, column=1, padx=10, pady=(20, 10), sticky="ew")
        add_context_menu(self.comfyui_url_entry)
        
        ctk.CTkLabel(self.comfyui_frame, text="Workflow Path (Optional):").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.comfyui_wf_entry = ctk.CTkEntry(self.comfyui_frame, placeholder_text="Leave empty for default")
        self.comfyui_wf_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        add_context_menu(self.comfyui_wf_entry)
        
        self.comfyui_status = ctk.CTkLabel(self.comfyui_frame, text="", text_color="gray")
        self.comfyui_status.grid(row=2, column=0, columnspan=2, pady=5)
        
        ctk.CTkButton(self.comfyui_frame, text="Test Connection", command=self._test_comfyui).grid(row=3, column=0, columnspan=2, pady=10)

        # Custom API Frame
        self.customapi_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.customapi_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.customapi_frame, text="API URL:").grid(row=0, column=0, padx=10, pady=(20, 10), sticky="e")
        self.api_url_entry = ctk.CTkEntry(self.customapi_frame, placeholder_text="https://api.openai.com/v1/images/generations")
        self.api_url_entry.grid(row=0, column=1, padx=10, pady=(20, 10), sticky="ew")
        add_context_menu(self.api_url_entry)
        
        ctk.CTkLabel(self.customapi_frame, text="API Key:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.api_key_entry = ctk.CTkEntry(self.customapi_frame, show="*")
        self.api_key_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        add_context_menu(self.api_key_entry)
        
        ctk.CTkLabel(self.customapi_frame, text="Model Name (Optional):").grid(row=2, column=0, padx=10, pady=10, sticky="e")
        self.api_model_entry = ctk.CTkEntry(self.customapi_frame, placeholder_text="dall-e-3")
        self.api_model_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        add_context_menu(self.api_model_entry)

        self.customapi_status = ctk.CTkLabel(self.customapi_frame, text="", text_color="gray")
        self.customapi_status.grid(row=3, column=0, columnspan=2, pady=5)
        
        ctk.CTkButton(self.customapi_frame, text="Test Connection", command=self._test_customapi).grid(row=4, column=0, columnspan=2, pady=10)

        # AI Video Provider Frame
        self.videoprovider_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.videoprovider_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.videoprovider_frame, text="Video API URL:").grid(row=0, column=0, padx=10, pady=(20, 10), sticky="e")
        self.video_url_entry = ctk.CTkEntry(self.videoprovider_frame, placeholder_text="https://api.openai.com/v1/videos/generations")
        self.video_url_entry.grid(row=0, column=1, padx=10, pady=(20, 10), sticky="ew")
        add_context_menu(self.video_url_entry)
        
        ctk.CTkLabel(self.videoprovider_frame, text="Video API Key:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.video_key_entry = ctk.CTkEntry(self.videoprovider_frame, show="*")
        self.video_key_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        add_context_menu(self.video_key_entry)
        
        ctk.CTkLabel(self.videoprovider_frame, text="Video Model:").grid(row=2, column=0, padx=10, pady=10, sticky="e")
        self.video_model_entry = ctk.CTkEntry(self.videoprovider_frame, placeholder_text="sora or runway-gen3 or luma-ray")
        self.video_model_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        add_context_menu(self.video_model_entry)
        
        self.video_status = ctk.CTkLabel(self.videoprovider_frame, text="", text_color="gray")
        self.video_status.grid(row=3, column=0, columnspan=2, pady=5)
        
        ctk.CTkButton(self.videoprovider_frame, text="Test Video API Connection", command=self._test_video_api).grid(row=4, column=0, columnspan=2, pady=10)

        # Free Stock Media (Pexels / Pixabay) Frame
        self.stockmedia_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.stockmedia_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.stockmedia_frame, text="Pexels API Key:").grid(row=0, column=0, padx=10, pady=(20, 10), sticky="e")
        self.pexels_key_entry = ctk.CTkEntry(self.stockmedia_frame, show="*", placeholder_text="Enter Pexels API Key")
        self.pexels_key_entry.grid(row=0, column=1, padx=10, pady=(20, 10), sticky="ew")
        add_context_menu(self.pexels_key_entry)
        
        self.pexels_status = ctk.CTkLabel(self.stockmedia_frame, text="", text_color="gray")
        self.pexels_status.grid(row=1, column=1, padx=10, pady=2, sticky="w")
        
        ctk.CTkButton(self.stockmedia_frame, text="Test Pexels Key", width=120, command=self._test_pexels).grid(row=2, column=1, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(self.stockmedia_frame, text="Pixabay API Key:").grid(row=3, column=0, padx=10, pady=(15, 10), sticky="e")
        self.pixabay_key_entry = ctk.CTkEntry(self.stockmedia_frame, show="*", placeholder_text="Enter Pixabay API Key")
        self.pixabay_key_entry.grid(row=3, column=1, padx=10, pady=(15, 10), sticky="ew")
        add_context_menu(self.pixabay_key_entry)
        
        self.pixabay_status = ctk.CTkLabel(self.stockmedia_frame, text="", text_color="gray")
        self.pixabay_status.grid(row=4, column=1, padx=10, pady=2, sticky="w")
        
        ctk.CTkButton(self.stockmedia_frame, text="Test Pixabay Key", width=120, command=self._test_pixabay).grid(row=5, column=1, padx=10, pady=5, sticky="w")

        # Quick Provider Test Frame
        self.quick_test_frame = ctk.CTkFrame(self, corner_radius=10)
        self.quick_test_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.quick_test_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self.quick_test_frame, text="Quick Provider Test", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, pady=(10, 5))
        
        qt_top = ctk.CTkFrame(self.quick_test_frame, fg_color="transparent")
        qt_top.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        ctk.CTkLabel(qt_top, text="Prompt Type:").pack(side="left", padx=(0, 10))
        self.prompt_type_var = ctk.StringVar(value="Positive Prompt")
        self.prompt_type_dropdown = ctk.CTkOptionMenu(
            qt_top,
            variable=self.prompt_type_var,
            values=["Positive Prompt"],
            command=self._on_prompt_type_change
        )
        self.prompt_type_dropdown.pack(side="left", fill="x", expand=True)
        
        self.btn_clear_prompt = ctk.CTkButton(qt_top, text="Clear", width=60, fg_color="#C0392B", hover_color="#922B21", command=self._clear_quick_prompt)
        self.btn_clear_prompt.pack(side="right", padx=(10, 0))
        
        self.prompt_textbox = ctk.CTkTextbox(self.quick_test_frame, height=100, fg_color="white", text_color="black")
        self.prompt_textbox.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        self.prompt_textbox.bind("<KeyRelease>", self._on_prompt_text_change)
        add_context_menu(self.prompt_textbox)
        
        self.quick_test_status = ctk.CTkLabel(self.quick_test_frame, text="", text_color="gray")
        self.quick_test_status.grid(row=3, column=0, pady=5)
        
        self.btn_generate_test = ctk.CTkButton(self.quick_test_frame, text="Generate Test Image", command=self._generate_test_image)
        self.btn_generate_test.grid(row=4, column=0, pady=(0, 10))

        # Bottom Buttons
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.grid(row=3, column=0, padx=20, pady=20, sticky="ew")
        
        ctk.CTkButton(bottom_frame, text="Cancel", fg_color="transparent", border_width=1, command=self.destroy).pack(side="left", expand=True, padx=5)
        ctk.CTkButton(bottom_frame, text="Save Settings", fg_color="#27AE60", hover_color="#229954", command=self._save_settings).pack(side="left", expand=True, padx=5)

    def _load_current_settings(self):
        comfyui_conf = self.settings.get("comfyui", {})
        self.comfyui_url_entry.insert(0, comfyui_conf.get("server_url", "http://127.0.0.1:8188"))
        self.comfyui_wf_entry.insert(0, comfyui_conf.get("workflow_path", ""))
        
        custom_conf = self.settings.get("custom_api", {})
        self.api_url_entry.insert(0, custom_conf.get("api_url", ""))
        self.api_key_entry.insert(0, custom_conf.get("api_key", ""))
        self.api_model_entry.insert(0, custom_conf.get("model_name", ""))

        video_conf = self.settings.get("video_provider", {})
        self.video_url_entry.insert(0, video_conf.get("api_url", ""))
        self.video_key_entry.insert(0, video_conf.get("api_key", ""))
        self.video_model_entry.insert(0, video_conf.get("model_name", ""))

        stock_conf = self.settings.get("stock_providers", {})
        self.pexels_key_entry.insert(0, stock_conf.get("pexels_api_key", ""))
        self.pixabay_key_entry.insert(0, stock_conf.get("pixabay_api_key", ""))
        
        self._on_provider_change(self.provider_var.get())

    def _on_provider_change(self, selected):
        self.builtin_frame.pack_forget()
        self.comfyui_frame.pack_forget()
        self.customapi_frame.pack_forget()
        self.videoprovider_frame.pack_forget()
        self.stockmedia_frame.pack_forget()
        
        if selected == "Built-in Provider":
            self.builtin_frame.pack(fill="both", expand=True)
            self.prompt_type_dropdown.configure(values=["Positive Prompt"])
            self.prompt_type_var.set("Positive Prompt")
            self._on_prompt_type_change("Positive Prompt")
        elif selected == "ComfyUI":
            self.comfyui_frame.pack(fill="both", expand=True)
            self.prompt_type_dropdown.configure(values=["Positive Prompt"])
            self.prompt_type_var.set("Positive Prompt")
            self._on_prompt_type_change("Positive Prompt")
        elif selected == "Custom API":
            self.customapi_frame.pack(fill="both", expand=True)
            self.prompt_type_dropdown.configure(values=["Positive Prompt"])
            self.prompt_type_var.set("Positive Prompt")
            self._on_prompt_type_change("Positive Prompt")
        elif selected == "AI Video Provider":
            self.videoprovider_frame.pack(fill="both", expand=True)
            self.prompt_type_dropdown.configure(values=["Positive Prompt"])
            self.prompt_type_var.set("Positive Prompt")
            self._on_prompt_type_change("Positive Prompt")
        elif selected == "Stock Media (Pexels/Pixabay)":
            self.stockmedia_frame.pack(fill="both", expand=True)
            self.prompt_type_dropdown.configure(values=["Positive Prompt"])
            self.prompt_type_var.set("Positive Prompt")
            self._on_prompt_type_change("Positive Prompt")

    def _test_comfyui(self):
        url = self.comfyui_url_entry.get().strip()
        if not url:
            self.comfyui_status.configure(text="Invalid URL", text_color="#E74C3C")
            return
            
        self.comfyui_status.configure(text="Testing...", text_color="white")
        self.update()
        
        try:
            req = urllib.request.Request(f"{url}/system_stats")
            urllib.request.urlopen(req, timeout=5)
            self.comfyui_status.configure(text="Connection Successful!", text_color="#2ECC71")
        except Exception as e:
            self.comfyui_status.configure(text=f"Connection Failed: {e}", text_color="#E74C3C")

    def _test_customapi(self):
        url = self.api_url_entry.get().strip()
        if not url:
            self.customapi_status.configure(text="Invalid URL", text_color="#E74C3C")
            return
        self.customapi_status.configure(text="Testing...", text_color="white")
        self.update()
        
        try:
            url = self.api_url_entry.get().strip()
            api_key = self.api_key_entry.get().strip()
            
            if "aihorde.net" in url:
                test_url = "https://aihorde.net/api/v2/status/models"
                headers = {
                    "apikey": api_key,
                    "Client-Agent": "AutoImageFlow:1.0:local",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            else:
                test_url = url
                headers = {"Authorization": f"Bearer {api_key}"}

            req = urllib.request.Request(test_url, headers=headers)
            try:
                urllib.request.urlopen(req, timeout=5)
                self.customapi_status.configure(text="Host is reachable!", text_color="#2ECC71")
            except urllib.error.HTTPError as e:
                if e.code in [401, 404, 405]:
                    self.customapi_status.configure(text=f"Host Reachable (HTTP {e.code})", text_color="#2ECC71")
                else:
                    self.customapi_status.configure(text=f"Host Reachable but returned HTTP {e.code}", text_color="#E74C3C")
        except Exception as e:
            self.customapi_status.configure(text=f"Connection Failed: {e}", text_color="#E74C3C")

    def _test_video_api(self):
        url = self.video_url_entry.get().strip()
        api_key = self.video_key_entry.get().strip()
        if not url:
            self.video_status.configure(text="Invalid Video API URL", text_color="#E74C3C")
            return
        self.video_status.configure(text="Testing...", text_color="white")
        self.update()

        try:
            headers = {"User-Agent": "AutoImageFlow/1.0"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            req = urllib.request.Request(url, headers=headers)
            try:
                urllib.request.urlopen(req, timeout=6)
                self.video_status.configure(text="Video API Host Reachable!", text_color="#2ECC71")
            except urllib.error.HTTPError as he:
                if he.code in [400, 401, 404, 405]:
                    self.video_status.configure(text=f"Endpoint Reachable (HTTP {he.code})", text_color="#2ECC71")
                else:
                    self.video_status.configure(text=f"Returned HTTP {he.code}", text_color="#E74C3C")
        except Exception as e:
            self.video_status.configure(text=f"Connection Failed: {e}", text_color="#E74C3C")

    def _test_pexels(self):
        key = self.pexels_key_entry.get().strip()
        if not key:
            self.pexels_status.configure(text="Please enter Pexels API Key", text_color="#E74C3C")
            return
        self.pexels_status.configure(text="Testing...", text_color="white")
        self.update()

        try:
            req = urllib.request.Request(
                "https://api.pexels.com/v1/curated?per_page=1",
                headers={"Authorization": key, "User-Agent": "AutoImageFlow/1.0"}
            )
            with urllib.request.urlopen(req, timeout=6) as resp:
                if resp.status == 200:
                    self.pexels_status.configure(text="Pexels API Key is Valid! (HTTP 200)", text_color="#2ECC71")
                else:
                    self.pexels_status.configure(text=f"HTTP {resp.status}", text_color="#E74C3C")
        except urllib.error.HTTPError as he:
            if he.code in (401, 403):
                self.pexels_status.configure(text="Invalid Pexels API Key", text_color="#E74C3C")
            else:
                self.pexels_status.configure(text=f"Error HTTP {he.code}", text_color="#E74C3C")
        except Exception as e:
            self.pexels_status.configure(text=f"Connection error: {e}", text_color="#E74C3C")

    def _test_pixabay(self):
        key = self.pixabay_key_entry.get().strip()
        if not key:
            self.pixabay_status.configure(text="Please enter Pixabay API Key", text_color="#E74C3C")
            return
        self.pixabay_status.configure(text="Testing...", text_color="white")
        self.update()

        try:
            test_url = f"https://pixabay.com/api/?key={key}&per_page=3&safesearch=true"
            req = urllib.request.Request(test_url, headers={"User-Agent": "AutoImageFlow/1.0"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                if resp.status == 200:
                    self.pixabay_status.configure(text="Pixabay API Key is Valid! (HTTP 200)", text_color="#2ECC71")
                else:
                    self.pixabay_status.configure(text=f"HTTP {resp.status}", text_color="#E74C3C")
        except urllib.error.HTTPError as he:
            if he.code in (400, 401, 403):
                self.pixabay_status.configure(text="Invalid Pixabay API Key", text_color="#E74C3C")
            else:
                self.pixabay_status.configure(text=f"Error HTTP {he.code}", text_color="#E74C3C")
        except Exception as e:
            self.pixabay_status.configure(text=f"Connection error: {e}", text_color="#E74C3C")

    def _save_settings(self):
        self.settings["active_provider"] = self.provider_var.get()
        
        if "comfyui" not in self.settings:
            self.settings["comfyui"] = {}
        self.settings["comfyui"]["server_url"] = self.comfyui_url_entry.get().strip()
        self.settings["comfyui"]["workflow_path"] = self.comfyui_wf_entry.get().strip()
        
        if "custom_api" not in self.settings:
            self.settings["custom_api"] = {}
        self.settings["custom_api"]["api_url"] = self.api_url_entry.get().strip()
        self.settings["custom_api"]["api_key"] = self.api_key_entry.get().strip()
        self.settings["custom_api"]["model_name"] = self.api_model_entry.get().strip()

        if "video_provider" not in self.settings:
            self.settings["video_provider"] = {}
        self.settings["video_provider"]["api_url"] = self.video_url_entry.get().strip()
        self.settings["video_provider"]["api_key"] = self.video_key_entry.get().strip()
        self.settings["video_provider"]["model_name"] = self.video_model_entry.get().strip()

        if "stock_providers" not in self.settings:
            self.settings["stock_providers"] = {}
        self.settings["stock_providers"]["pexels_api_key"] = self.pexels_key_entry.get().strip()
        self.settings["stock_providers"]["pixabay_api_key"] = self.pixabay_key_entry.get().strip()
        
        save_settings(self.settings)
        if self.on_save_callback:
            self.on_save_callback(self.settings)
            
        self.destroy()

    def _on_prompt_type_change(self, selected):
        self.prompt_textbox.delete("1.0", "end")
        if selected == "Positive Prompt":
            self.prompt_textbox.insert("1.0", self.test_positive_prompt)
        elif selected == "Negative Prompt":
            self.prompt_textbox.insert("1.0", self.test_negative_prompt)

    def _clear_quick_prompt(self):
        self.prompt_textbox.delete("1.0", "end")
        self._on_prompt_text_change()

    def _on_prompt_text_change(self, event=None):
        val = self.prompt_textbox.get("1.0", "end-1c")
        if self.prompt_type_var.get() == "Positive Prompt":
            self.test_positive_prompt = val
        elif self.prompt_type_var.get() == "Negative Prompt":
            self.test_negative_prompt = val

    def _generate_test_image(self):
        provider = self.provider_var.get()
        # Save temporary settings
        self.settings["active_provider"] = provider
        if "comfyui" not in self.settings: self.settings["comfyui"] = {}
        self.settings["comfyui"]["server_url"] = self.comfyui_url_entry.get().strip()
        self.settings["comfyui"]["workflow_path"] = self.comfyui_wf_entry.get().strip()
        if "custom_api" not in self.settings: self.settings["custom_api"] = {}
        self.settings["custom_api"]["api_url"] = self.api_url_entry.get().strip()
        self.settings["custom_api"]["api_key"] = self.api_key_entry.get().strip()
        self.settings["custom_api"]["model_name"] = self.api_model_entry.get().strip()

        # Update text from textbox just in case
        self._on_prompt_text_change()

        prompt = self.test_positive_prompt
        if not prompt.strip():
            self.quick_test_status.configure(text="Please enter a prompt.", text_color="#E74C3C")
            return

        self.btn_generate_test.configure(state="disabled")
        self.quick_test_status.configure(text="Initializing...", text_color="white")

        import threading
        threading.Thread(target=self._run_test_generation, args=(provider, prompt), daemon=True).start()

    def _run_test_generation(self, provider, prompt):
        from core.web_automation import WebAutomationRunner
        from core.comfy_client import ComfyUIClient
        from core.custom_api_client import CustomAPIClient
        from core.horde_client import HordeClient
        from utils.config_manager import load_generators
        import os

        download_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        runner = None
        
        try:
            if provider == "Built-in Provider":
                generators = load_generators()
                gen_id = self.master.gen_var.get() if hasattr(self.master, 'gen_var') else None
                config = next((g for g in generators if g["id"] == gen_id), generators[0] if generators else None)
                if not config:
                    self._update_test_status("No built-in config found.", "#E74C3C")
                    return
                runner = WebAutomationRunner(config, download_folder)
            elif provider == "ComfyUI":
                config = {
                    "type": "comfyui_provider",
                    "url": self.settings["comfyui"]["server_url"],
                    "workflow_path": self.settings["comfyui"]["workflow_path"]
                }
                runner = ComfyUIClient(config, download_folder)
            elif provider == "Custom API":
                mode = self.master.mode_var.get() if hasattr(self.master, 'mode_var') else "Free Generator"
                api_url = self.settings.get("custom_api", {}).get("api_url", "")
                
                # Auto-detect AI Horde if they haven't restarted or selected the radio button
                if mode == "AI Horde Automation" or "aihorde.net" in api_url:
                    config = {
                        "type": "ai_horde",
                        "api_key": self.settings["custom_api"]["api_key"],
                        "model_selection": self.settings["custom_api"]["model_name"]
                    }
                    runner = HordeClient(config, download_folder)
                else:
                    config = {
                        "type": "custom_api",
                        "api_url": self.settings["custom_api"]["api_url"],
                        "api_key": self.settings["custom_api"]["api_key"],
                        "model_name": self.settings["custom_api"]["model_name"]
                    }
                    runner = CustomAPIClient(config, download_folder)
            elif provider == "AI Video Provider":
                from core.video_providers.generic_video_client import GenericVideoClient
                video_conf = self.settings.get("video_provider", {})
                config = {
                    "type": "video_provider",
                    "api_url": video_conf.get("api_url", ""),
                    "api_key": video_conf.get("api_key", ""),
                    "model_name": video_conf.get("model_name", "sora")
                }
                runner = GenericVideoClient(config, download_folder)
            elif provider == "Stock Media (Pexels/Pixabay)":
                from core.stock_providers.pexels_client import PexelsClient
                from core.stock_providers.pixabay_client import PixabayClient
                stock_conf = self.settings.get("stock_providers", {})
                if stock_conf.get("pexels_api_key"):
                    client = PexelsClient(stock_conf.get("pexels_api_key"), download_folder)
                else:
                    client = PixabayClient(stock_conf.get("pixabay_api_key"), download_folder)
                res = client.search_and_download(prompt, count=1, progress_callback=self._test_progress_callback)
                if res.get("success") and res.get("downloaded_files"):
                    self._update_test_status("Stock media downloaded successfully!", "#2ECC71")
                else:
                    self._update_test_status(f"Download failed: {res.get('error', 'No media found')}", "#E74C3C")
                self.after(0, lambda: self.btn_generate_test.configure(state="normal"))
                return

            if runner and hasattr(runner, 'startup'):
                runner.startup(self._test_progress_callback)

            if runner:
                success = runner.generate_and_download(
                    prompt, 
                    auto_name=True, 
                    auto_download=True, 
                    progress_callback=self._test_progress_callback
                )
                if success:
                    self._update_test_status("Test image generated successfully!", "#2ECC71")
                else:
                    self._update_test_status("Generation failed.", "#E74C3C")
            else:
                self._update_test_status("Failed to initialize runner.", "#E74C3C")

        except Exception as e:
            self._update_test_status(f"Error: {e}", "#E74C3C")
        finally:
            if runner and hasattr(runner, 'shutdown'):
                runner.shutdown()
            self.after(0, lambda: self.btn_generate_test.configure(state="normal"))

    def _test_progress_callback(self, percent, text):
        self.after(0, lambda: self.quick_test_status.configure(text=text, text_color="white"))

    def _update_test_status(self, text, color):
        self.after(0, lambda: self.quick_test_status.configure(text=text, text_color=color))
