#!/usr/bin/env python3
import shutil
import os
import tqdm
root_path = "/storage/suchka-storage/pornpics/"
# list all folders in the output folder
folders = [f for f in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, f))]
folders = sorted(folders, key=lambda f: f)
for gid in tqdm.tqdm(folders, desc="Scanning galleries"):
  data_file = os.path.join(root_path, gid, 'data.json')
  if not os.path.exists(data_file):
    print(gid)
    shutil.rmtree(os.path.join(root_path, gid))