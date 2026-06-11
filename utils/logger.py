import logging
import os

import sys

if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.dirname(__file__))

LOG_FILE = os.path.join(base_dir, "app.log")

# Setup logger
logger = logging.getLogger("AutoImageFlow")
logger.setLevel(logging.INFO)

# File handler
fh = logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8')
fh.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
fh.setFormatter(formatter)

# Add handler to logger
logger.addHandler(fh)

def get_logger():
    return logger
