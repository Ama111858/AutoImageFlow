import customtkinter as ctk
from tkinter import filedialog
import os

from core.engine import AutomationEngine
from utils.config_manager import load_generators
from utils.file_utils import read_prompts_from_file
from utils.settings_manager import load_settings, save_settings
from ui.settings_window import SettingsWindow
from utils.ui_utils import add_context_menu
import tkinter.messagebox as messagebox

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class EngineCallbacks:
    def __init__(self, app):
        self.app = app

    def on_status_change(self, status):
        self.app.update_status(status)

    def on_queue_update(self, count):
        self.app.update_queue_count(count)

    def on_progress_update(self, percent, text):
        self.app.update_progress(percent, text)

    def on_prompt_completed(self):
        self.app.increment_completed()

    def on_prompt_failed(self):
        self.app.increment_failed()

class AutoImageFlowApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("AutoImageFlow - AI Dashboard")
        self.geometry("1000x700")
        self.configure(fg_color="#1E1E1E")
        
        self.callbacks = EngineCallbacks(self)
        self.engine = AutomationEngine(self.callbacks)
        self.generators = load_generators()
        self.settings = load_settings()
        
        self.completed_count = 0
        self.failed_count = 0
        
        self._setup_ui()
        self._populate_generators()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # LEFT PANEL (Prompt Queue)
        self.left_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#2B2B2B", border_color="#E53935", border_width=1)
        self.left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.left_frame.grid_rowconfigure(2, weight=1)
        
        self.queue_label = ctk.CTkLabel(self.left_frame, text="Prompt Queue (0)", font=ctk.CTkFont(size=18, weight="bold"), text_color="#FFFFFF")
        self.queue_label.grid(row=0, column=0, padx=10, pady=(10,5), sticky="w")
        
        btn_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        btn_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkButton(btn_frame, text="Import .txt", command=self.import_txt, width=100, fg_color="#E53935", hover_color="#FF5252").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Clear", command=self.clear_queue, width=100, fg_color="#F44336", hover_color="#FF5252").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Add to Queue", command=self.add_from_textbox, width=100, fg_color="#E53935", hover_color="#FF5252").pack(side="left", padx=5)

        self.prompt_textbox = ctk.CTkTextbox(self.left_frame, corner_radius=10, fg_color="#2B2B2B", text_color="#FFFFFF", border_color="#E53935", border_width=2)
        self.prompt_textbox.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        add_context_menu(self.prompt_textbox)


        # RIGHT PANEL (Controls & Dashboard)
        self.right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.right_frame.grid_columnconfigure(0, weight=1)

        # 1. Generator Selection
        self.gen_frame = ctk.CTkFrame(self.right_frame, corner_radius=15, fg_color="#2B2B2B", border_color="#E53935", border_width=1)
        self.gen_frame.grid(row=0, column=0, pady=(0, 10), sticky="ew")
        ctk.CTkLabel(self.gen_frame, text="Generator Selection", font=ctk.CTkFont(size=18, weight="bold"), text_color="#FFFFFF").pack(anchor="w", padx=10, pady=(10,5))
        
        # Mode Toggle
        self.mode_var = ctk.StringVar(value=self.settings.get("active_mode", "Free Generator"))
        self.mode_frame = ctk.CTkFrame(self.gen_frame, fg_color="transparent")
        self.mode_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(self.mode_frame, text="Mode:", text_color="#BDBDBD").pack(side="left", padx=(0, 10))
        self.mode_dropdown = ctk.CTkOptionMenu(
            self.mode_frame,
            values=["Free Generator", "AI Horde Automation", "AI Video Generation", "Free Stock Media (Pexels / Pixabay)"],
            variable=self.mode_var,
            command=lambda v: self._on_mode_change(),
            fg_color="#1E1E1E", button_color="#E53935", button_hover_color="#FF5252", text_color="#FFFFFF"
        )
        self.mode_dropdown.pack(side="left", fill="x", expand=True)

        # Generator List (only for Free Generator)
        self.gen_var = ctk.StringVar(value="")
        self.gen_radio_frame = ctk.CTkFrame(self.gen_frame, fg_color="transparent")
        self.gen_radio_frame.pack(fill="x", padx=10, pady=5)
        
        btn_gen_frame = ctk.CTkFrame(self.gen_frame, fg_color="transparent")
        btn_gen_frame.pack(fill="x", padx=10, pady=(0, 5))
        ctk.CTkButton(btn_gen_frame, text="Settings", command=self.open_settings, width=80, fg_color="#E53935", hover_color="#FF5252").pack(side="left")
        ctk.CTkButton(btn_gen_frame, text="Edit Config", command=self.edit_generators, width=80, fg_color="#E53935", hover_color="#FF5252").pack(side="left", padx=5)
        ctk.CTkButton(btn_gen_frame, text="Reload", command=self.reload_generators, width=80, fg_color="#E53935", hover_color="#FF5252").pack(side="left")

        # Aspect Ratio Selection
        self.ar_frame = ctk.CTkFrame(self.gen_frame, fg_color="transparent")
        self.ar_frame.pack(fill="x", padx=10, pady=(5, 10))
        ctk.CTkLabel(self.ar_frame, text="Aspect Ratio:", text_color="#BDBDBD").pack(side="left")
        self.aspect_ratio_var = ctk.StringVar(value=self.settings.get("default_aspect_ratio", "1:1"))
        self.aspect_ratio_var.trace_add("write", lambda *args: self._save_aspect_ratio())
        self.ar_combo = ctk.CTkComboBox(
            self.ar_frame, 
            values=["1:1", "4:3", "3:4", "16:9", "9:16"], 
            variable=self.aspect_ratio_var, 
            state="readonly", 
            width=100,
            fg_color="#1E1E1E", border_color="#E53935", button_color="#E53935", button_hover_color="#FF5252"
        )
        self.ar_combo.pack(side="left", padx=10)
        
        # Model Selection
        self.model_frame = ctk.CTkFrame(self.gen_frame, fg_color="transparent")
        self.model_frame.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkLabel(self.model_frame, text="Model:", text_color="#BDBDBD").pack(side="left", padx=(0, 24))
        self.model_var = ctk.StringVar(value=self.settings.get("default_model", "DreamShaper"))
        self.model_var.trace_add("write", lambda *args: self._save_model_selection())
        self.model_combo = ctk.CTkComboBox(
            self.model_frame,
            values=["DreamShaper", "Realistic Vision"],
            variable=self.model_var,
            state="readonly",
            width=200,
            fg_color="#1E1E1E", border_color="#E53935", button_color="#E53935", button_hover_color="#FF5252"
        )
        self.model_combo.pack(side="left")

        # Video Configuration Frame
        self.video_config_frame = ctk.CTkFrame(self.gen_frame, fg_color="transparent")
        ctk.CTkLabel(self.video_config_frame, text="Duration:", text_color="#BDBDBD").pack(side="left")
        self.video_duration_var = ctk.StringVar(value="5s")
        self.video_duration_combo = ctk.CTkComboBox(
            self.video_config_frame,
            values=["5s", "10s", "15s"],
            variable=self.video_duration_var,
            state="readonly",
            width=80,
            fg_color="#1E1E1E", border_color="#E53935", button_color="#E53935", button_hover_color="#FF5252"
        )
        self.video_duration_combo.pack(side="left", padx=(5, 15))

        # Stock Media Configuration Frame
        self.stock_config_frame = ctk.CTkFrame(self.gen_frame, fg_color="transparent")
        
        stock_row1 = ctk.CTkFrame(self.stock_config_frame, fg_color="transparent")
        stock_row1.pack(fill="x", pady=2)
        ctk.CTkLabel(stock_row1, text="Source:", text_color="#BDBDBD").pack(side="left")
        self.stock_provider_var = ctk.StringVar(value="Pexels")
        self.stock_provider_combo = ctk.CTkComboBox(
            stock_row1,
            values=["Pexels", "Pixabay"],
            variable=self.stock_provider_var,
            state="readonly",
            width=100,
            fg_color="#1E1E1E", border_color="#E53935", button_color="#E53935", button_hover_color="#FF5252"
        )
        self.stock_provider_combo.pack(side="left", padx=(5, 15))

        ctk.CTkLabel(stock_row1, text="Type:", text_color="#BDBDBD").pack(side="left")
        self.stock_media_type_var = ctk.StringVar(value="Photos")
        self.stock_media_type_combo = ctk.CTkComboBox(
            stock_row1,
            values=["Photos", "Videos"],
            variable=self.stock_media_type_var,
            state="readonly",
            width=100,
            fg_color="#1E1E1E", border_color="#E53935", button_color="#E53935", button_hover_color="#FF5252"
        )
        self.stock_media_type_combo.pack(side="left", padx=5)

        stock_row2 = ctk.CTkFrame(self.stock_config_frame, fg_color="transparent")
        stock_row2.pack(fill="x", pady=4)
        ctk.CTkLabel(stock_row2, text="Count:", text_color="#BDBDBD").pack(side="left")
        self.stock_count_var = ctk.StringVar(value="2")
        self.stock_count_combo = ctk.CTkComboBox(
            stock_row2,
            values=["1", "2", "3", "5", "10"],
            variable=self.stock_count_var,
            state="readonly",
            width=70,
            fg_color="#1E1E1E", border_color="#E53935", button_color="#E53935", button_hover_color="#FF5252"
        )
        self.stock_count_combo.pack(side="left", padx=(5, 15))

        ctk.CTkLabel(stock_row2, text="Orientation:", text_color="#BDBDBD").pack(side="left")
        self.stock_orientation_var = ctk.StringVar(value="Any")
        self.stock_orientation_combo = ctk.CTkComboBox(
            stock_row2,
            values=["Any", "Landscape", "Portrait", "Square"],
            variable=self.stock_orientation_var,
            state="readonly",
            width=100,
            fg_color="#1E1E1E", border_color="#E53935", button_color="#E53935", button_hover_color="#FF5252"
        )
        self.stock_orientation_combo.pack(side="left", padx=5)
        # 2. Download Manager
        self.dl_frame = ctk.CTkFrame(self.right_frame, corner_radius=15, fg_color="#2B2B2B", border_color="#E53935", border_width=1)
        self.dl_frame.grid(row=1, column=0, pady=10, sticky="ew")
        ctk.CTkLabel(self.dl_frame, text="Download Manager", font=ctk.CTkFont(size=18, weight="bold"), text_color="#FFFFFF").pack(anchor="w", padx=10, pady=(10,5))
        
        dl_inner = ctk.CTkFrame(self.dl_frame, fg_color="transparent")
        dl_inner.pack(fill="x", padx=10, pady=5)
        
        dl_settings = self.settings.get("download_manager", {})
        default_dl = dl_settings.get("folder", os.path.join(os.path.expanduser("~"), "Downloads"))
        self.dl_folder_var = ctk.StringVar(value=default_dl)
        self.dl_folder_var.trace_add("write", lambda *args: self._save_dl_settings())
        
        ctk.CTkLabel(dl_inner, text="Folder:", text_color="#BDBDBD").pack(side="left", padx=5)
        self.dl_folder_entry = ctk.CTkEntry(dl_inner, textvariable=self.dl_folder_var, width=200, fg_color="#1E1E1E", border_color="#E53935", text_color="#FFFFFF")
        self.dl_folder_entry.pack(side="left", padx=5, fill="x", expand=True)
        add_context_menu(self.dl_folder_entry)
        ctk.CTkButton(dl_inner, text="Browse", width=80, command=self.browse_folder, fg_color="#E53935", hover_color="#FF5252").pack(side="left", padx=5)
        
        toggles_frame = ctk.CTkFrame(self.dl_frame, fg_color="transparent")
        toggles_frame.pack(fill="x", padx=10, pady=(5, 10))
        self.auto_name_switch = ctk.CTkSwitch(toggles_frame, text="Auto-name files", command=self._save_dl_settings, progress_color="#E53935", text_color="#BDBDBD")
        if dl_settings.get("auto_name", True):
            self.auto_name_switch.select()
        else:
            self.auto_name_switch.deselect()
        self.auto_name_switch.pack(side="left", padx=10)
        
        self.auto_dl_switch = ctk.CTkSwitch(toggles_frame, text="Auto-download", command=self._save_dl_settings, progress_color="#E53935", text_color="#BDBDBD")
        if dl_settings.get("auto_download", True):
            self.auto_dl_switch.select()
        else:
            self.auto_dl_switch.deselect()
        self.auto_dl_switch.pack(side="left", padx=10)


        # 3. Progress Dashboard
        self.dash_frame = ctk.CTkFrame(self.right_frame, corner_radius=15, fg_color="#2B2B2B", border_color="#E53935", border_width=1)
        self.dash_frame.grid(row=2, column=0, pady=10, sticky="ew")
        ctk.CTkLabel(self.dash_frame, text="Progress Dashboard", font=ctk.CTkFont(size=18, weight="bold"), text_color="#FFFFFF").pack(anchor="w", padx=10, pady=(10,5))
        
        stats_frame = ctk.CTkFrame(self.dash_frame, fg_color="transparent")
        stats_frame.pack(fill="x", padx=10, pady=5)
        self.status_lbl = ctk.CTkLabel(stats_frame, text="Status: Stopped", font=ctk.CTkFont(weight="bold"), text_color="#FFFFFF")
        self.status_lbl.pack(side="left", padx=10)
        self.completed_lbl = ctk.CTkLabel(stats_frame, text="Completed: 0", text_color="#4CAF50")
        self.completed_lbl.pack(side="left", padx=10)
        self.failed_lbl = ctk.CTkLabel(stats_frame, text="Failed: 0", text_color="#F44336")
        self.failed_lbl.pack(side="left", padx=10)
        
        self.progress_bar = ctk.CTkProgressBar(self.dash_frame, progress_color="#E53935")
        self.progress_bar.pack(fill="x", padx=10, pady=10)
        self.progress_bar.set(0)
        self.progress_text = ctk.CTkLabel(self.dash_frame, text="Ready", text_color="#BDBDBD")
        self.progress_text.pack(pady=(0, 10))

        # 4. Controls
        self.ctrl_frame = ctk.CTkFrame(self.right_frame, corner_radius=15, fg_color="#2B2B2B", border_color="#E53935", border_width=1)
        self.ctrl_frame.grid(row=3, column=0, pady=(10,0), sticky="ew")
        
        btn_container = ctk.CTkFrame(self.ctrl_frame, fg_color="transparent")
        btn_container.pack(pady=15)
        ctk.CTkButton(btn_container, text="Start", command=self.start_engine, fg_color="#4CAF50", hover_color="#388E3C").pack(side="left", padx=10)
        ctk.CTkButton(btn_container, text="Pause", command=self.pause_engine, fg_color="#FFB300", hover_color="#FF8F00").pack(side="left", padx=10)
        ctk.CTkButton(btn_container, text="Stop", command=self.stop_engine, fg_color="#F44336", hover_color="#D32F2F").pack(side="left", padx=10)

    def _populate_generators(self):
        for widget in self.gen_radio_frame.winfo_children():
            widget.destroy()
            
        if not self.generators:
            ctk.CTkLabel(self.gen_radio_frame, text="No generators found in config.json", text_color="#F44336").pack(anchor="w")
            return
            
        for gen in self.generators:
            rb = ctk.CTkRadioButton(self.gen_radio_frame, text=gen["name"], variable=self.gen_var, value=gen["id"], text_color="#BDBDBD", fg_color="#E53935", hover_color="#FF5252")
            rb.pack(anchor="w", pady=2)
            
        self.gen_var.set(self.generators[0]["id"])
        self._on_mode_change()

    def _on_mode_change(self):
        mode = self.mode_var.get()
        self.settings["active_mode"] = mode
        save_settings(self.settings)

        self.gen_radio_frame.pack_forget()
        self.ar_frame.pack_forget()
        self.model_frame.pack_forget()
        self.video_config_frame.pack_forget()
        self.stock_config_frame.pack_forget()

        if mode == "Free Generator":
            self.gen_radio_frame.pack(fill="x", padx=10, pady=5)
            self.ar_frame.pack(fill="x", padx=10, pady=(5, 10))
        elif mode == "AI Horde Automation":
            self.model_frame.pack(fill="x", padx=10, pady=(0, 10))
            self.ar_frame.pack(fill="x", padx=10, pady=(5, 10))
        elif mode == "AI Video Generation":
            self.video_config_frame.pack(fill="x", padx=10, pady=(5, 10))
            self.ar_frame.pack(fill="x", padx=10, pady=(5, 10))
        elif mode == "Free Stock Media (Pexels / Pixabay)":
            self.stock_config_frame.pack(fill="x", padx=10, pady=(5, 10))

    def import_txt(self):
        filepath = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if filepath:
            prompts = read_prompts_from_file(filepath)
            self.prompt_textbox.insert("end", "\n".join(prompts) + "\n")

    def clear_queue(self):
        self.prompt_textbox.delete("1.0", "end")
        self.engine.clear_queue()
        
    def add_from_textbox(self):
        text = self.prompt_textbox.get("1.0", "end")
        prompts = [p.strip() for p in text.split("\n") if p.strip()]
        self.engine.add_prompts(prompts)
        self.prompt_textbox.delete("1.0", "end")

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.dl_folder_var.set(folder)

    def start_engine(self):
        mode = self.mode_var.get()
        
        if mode == "Free Generator":
            provider = self.settings.get("active_provider", "Built-in Provider")
            if provider == "Built-in Provider":
                gen_id = self.gen_var.get()
                config = next((g for g in self.generators if g["id"] == gen_id), None)
                if not config:
                    messagebox.showerror("Error", "No generator config found for Built-in Provider.")
                    return
                self.engine.set_generator_config(config)
            elif provider == "ComfyUI":
                comfy_conf = self.settings.get("comfyui", {})
                config = {
                    "type": "comfyui_provider",
                    "url": comfy_conf.get("server_url", "http://127.0.0.1:8188"),
                    "workflow_path": comfy_conf.get("workflow_path", ""),
                    "model_selection": self.model_var.get()
                }
                self.engine.set_generator_config(config)
            elif provider == "Custom API":
                api_conf = self.settings.get("custom_api", {})
                config = {
                    "type": "custom_api",
                    "api_url": api_conf.get("api_url", ""),
                    "api_key": api_conf.get("api_key", ""),
                    "model_name": api_conf.get("model_name", "")
                }
                self.engine.set_generator_config(config)

        elif mode == "AI Horde Automation":
            api_conf = self.settings.get("custom_api", {})
            config = {
                "type": "ai_horde",
                "api_key": api_conf.get("api_key", ""),
                "model_selection": self.model_var.get()
            }
            self.engine.set_generator_config(config)

        elif mode == "AI Video Generation":
            video_conf = self.settings.get("video_provider", {})
            config = {
                "type": "video_provider",
                "api_url": video_conf.get("api_url", ""),
                "api_key": video_conf.get("api_key", ""),
                "model_name": video_conf.get("model_name", "sora"),
                "duration": self.video_duration_var.get(),
                "aspect_ratio": self.aspect_ratio_var.get()
            }
            self.engine.set_generator_config(config)

        elif mode == "Free Stock Media (Pexels / Pixabay)":
            stock_conf = self.settings.get("stock_providers", {})
            provider = self.stock_provider_var.get().lower()
            api_key = stock_conf.get(f"{provider}_api_key", "")
            orient = self.stock_orientation_var.get().lower()
            config = {
                "type": "stock_provider",
                "provider": provider,
                "api_key": api_key,
                "media_type": self.stock_media_type_var.get().lower(),
                "count": int(self.stock_count_var.get()),
                "orientation": None if orient == "any" else orient
            }
            self.engine.set_generator_config(config)
        self.engine.set_download_settings(
            self.dl_folder_var.get(),
            self.auto_name_switch.get() == 1,
            self.auto_dl_switch.get() == 1
        )
        self.engine.set_aspect_ratio(self.aspect_ratio_var.get())
        self.engine.start()

    def pause_engine(self):
        self.engine.pause()

    def stop_engine(self):
        self.engine.stop()

    def update_status(self, status):
        self.after(0, lambda: self.status_lbl.configure(text=f"Status: {status}"))

    def update_queue_count(self, count):
        self.after(0, lambda: self.queue_label.configure(text=f"Prompt Queue ({count})"))

    def edit_generators(self):
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "generators.json")
        try:
            os.startfile(config_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open config: {e}")

    def reload_generators(self):
        self.generators = load_generators()
        self._populate_generators()

    def _save_dl_settings(self):
        self.settings["download_manager"] = {
            "folder": self.dl_folder_var.get(),
            "auto_name": self.auto_name_switch.get() == 1,
            "auto_download": self.auto_dl_switch.get() == 1
        }
        save_settings(self.settings)

    def _save_aspect_ratio(self):
        self.settings["default_aspect_ratio"] = self.aspect_ratio_var.get()
        save_settings(self.settings)

    def _save_model_selection(self):
        self.settings["default_model"] = self.model_var.get()
        save_settings(self.settings)

    def open_settings(self):
        SettingsWindow(self, self.settings, self._on_settings_saved)

    def _on_settings_saved(self, new_settings):
        self.settings = new_settings

    def update_progress(self, percent, text):
        self.after(0, lambda: self.progress_bar.set(percent / 100.0))
        self.after(0, lambda: self.progress_text.configure(text=text))

    def increment_completed(self):
        self.completed_count += 1
        self.after(0, lambda: self.completed_lbl.configure(text=f"Completed: {self.completed_count}"))

    def increment_failed(self):
        self.failed_count += 1
        self.after(0, lambda: self.failed_lbl.configure(text=f"Failed: {self.failed_count}"))
