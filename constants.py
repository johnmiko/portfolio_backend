import logging
import os
from pathlib import Path

GLOBAL_LOG_LEVEL = logging.INFO
# PROJ_DIR = os.path.dirname(os.path.abspath(Path(__file__).parent))
PROJ_DIR = os.path.dirname(os.path.abspath(Path(__file__)))
DOTA_DIR = PROJ_DIR + '/dota/'
print('dota dir')
print(DOTA_DIR)
