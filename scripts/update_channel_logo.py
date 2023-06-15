#!/usr/bin/env python3
import os
import sys
import traceback
import time

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

import tqdm

from dotenv import load_dotenv
load_dotenv()

project_storage_root = os.getenv("PROJECT_STORAGE_PATH")
channel_logo_dir = f"{project_storage_root}/channels"

logo_files = []
logo_files += [os.path.join(root, file) for root, dirs, files in os.walk(channel_logo_dir+'/jpg') for file in files if file.endswith((".jpg", ".png"))]
logo_files += [os.path.join(root, file) for root, dirs, files in os.walk(channel_logo_dir+'/png') for file in files if file.endswith((".jpg", ".png"))]

for logo in logo_files:
  print(logo)