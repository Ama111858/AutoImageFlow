# Auto Bulk Image Generator V3

Auto Bulk Image Generator V3 is a powerful, GUI-based automation tool for generating images in bulk. It seamlessly integrates with various generation engines, allowing you to queue prompts and download images automatically.

## Features
- **Multi-Provider Architecture**: Supports Built-in Automation, ComfyUI, and Custom APIs natively.
- **Bulk Queue Processing**: Import text files with prompts and automatically generate images sequentially.
- **Download Manager**: Automatically names and downloads images to your selected folder.
- **Quick Provider Testing**: Easily test your configured provider with positive/negative prompts without starting a full queue.
- **Windows Standalone Build**: Easily compile to a native Windows Executable for portability.

## Installation

### Method 1: Using the Standalone Executable (Windows)
1. Download the latest `.exe` release from the GitHub Releases page.
2. Run the executable. No installation required!

### Method 2: Running from Source
1. Clone this repository.
2. Install Python 3.10+
3. Install the required dependencies:
   ```cmd
   pip install -r requirements.txt
   ```
4. Run the application:
   ```cmd
   python main.py
   ```

### Method 3: Building your own Executable
1. Install requirements as shown in Method 2.
2. Run the build script:
   ```cmd
   python build.py
   ```
3. Your standalone executable will be generated in the `dist/` folder.

## Configuration
Access the **Settings** panel within the application to configure your active provider:
- **Built-in Provider**: Uses web automation templates (`config/generators.json`).
- **ComfyUI**: Provide your local or remote ComfyUI URL (e.g., `http://127.0.0.1:8188`). You can optionally specify a custom `workflow_api.json` path.
- **Custom API**: Provide an API URL (OpenAI-compatible) and API key to connect to customized cloud APIs.

## Known Issues

**Mode Switching Refresh**
After switching between Online Mode and ComfyUI Mode in the settings, the previous workflow state may occasionally remain active if the engine was already running.

**Workaround:**
1. Click **Stop** to halt the current queue.
2. Run a **Test Generation** in the Settings menu to prime the new mode.
3. Switch back to the main UI and click **Start** to continue normal generation with the correct workflow.

## Screenshots
*(Add screenshots here)*
![Main UI](screenshots/main_ui.png)
![Settings](screenshots/settings.png)

## License
MIT License.
