#!/usr/bin/env python3
import shutil
import os
import tqdm
root_path = "/storage/suchka-storage/pornpics/"
deleted_folders = 0
# list all folders in the output folder
folders = [f for f in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, f))]
folders = sorted(folders, key=lambda f: f)
for gid in tqdm.tqdm(folders, desc="Scanning galleries"):
  data_file = os.path.join(root_path, gid, 'data.json')
  if not os.path.exists(data_file):
    print(f'Deleting {gid}\t total deleted: {deleted_folders}')
    deleted_folders += 1
    shutil.rmtree(os.path.join(root_path, gid))
print(f'Total deleted: {deleted_folders} folders')