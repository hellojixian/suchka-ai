import shutil
import os
root_path = os.path.dirname(os.getcwd())+"/output/pornpics/"
# list all folders in the output folder
folders = [f for f in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, f))]
for gid in folders:
  data_file = os.path.join(root_path, gid, 'data.json')
  if not os.path.exists(data_file):
    print(gid)
    shutil.rmtree(os.path.join(root_path, gid))