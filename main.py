import sys
import os

# Add the project root to sys.path so 'core', 'ui', 'utils' are importable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.app import AutoImageFlowApp

def main():
    app = AutoImageFlowApp()
    app.mainloop()

if __name__ == "__main__":
    main()
