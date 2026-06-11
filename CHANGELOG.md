# Changelog

## [3.0.0] - Auto Bulk Image Generator V3

### Added
- **Multi-Provider Architecture**: Support for Built-in Provider, ComfyUI Local/Remote server, and Custom API generation endpoints.
- **Quick Test Panel**: Added a convenient Quick Test interface in the Settings window to test individual prompts (positive and negative) without affecting the bulk queue.
- **Settings GUI**: A dedicated settings dialog to manage Active Provider choices and their configurations, completely eliminating the need for manual JSON editing.
- **Context Menus**: All text inputs now fully support native copy, paste, cut, select all, and clear functionalities via a simple right-click context menu.
- **Error Handling**: Replaced generic console messages with proper, user-friendly GUI error popups. Added background logging via `app.log` to preserve critical errors without displaying console windows.
- **Build System**: Added a `build.py` script to seamlessly generate a Windows-ready standalone `.exe` using PyInstaller.

### Changed
- Re-architected `AutomationEngine` to dynamically switch runners (`WebAutomationRunner`, `ComfyUIClient`, `CustomAPIClient`) based on active provider configuration.
- UI settings such as the Download Folder path and Auto-download switches now automatically save their state persistently.
- Cleaned up source tree, removing temporary directories, batch scripts, and unnecessary logs.

### Fixed
- Fixed bug where `CTkTextbox` swallowed copy/paste events from the right-click menu.
