#!/usr/bin/env python3
import json
import os
import piexif
from PIL import Image
root_path = os.path.dirname(os.getcwd())+"/output/pornpics/"
# list all folders in the output folder
folders = [f for f in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, f))]
for gid in folders:
  g_folder = os.path.join(root_path, gid)
  data_file = os.path.join(g_folder, 'data.json')
  if not os.path.exists(data_file): continue
  with open(data_file, "r") as f:
    data = json.load(f)
  if "url" not in data:
    print(f"{gid} is missing url")
