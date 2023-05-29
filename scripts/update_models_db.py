#!/usr/bin/env python3

# scan the specified folder for images and create a database of faces
# create a status file to track the progress of the scan

# build unique model name list
# each model create a new entity in the database

import os
import sys
import json
import tqdm

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

import core.data_schema.model as model
from core.database import Database
db = Database()

input_folder = sys.argv[1]


processed_galleries = [g[0].path for g in model.Model.objects.values_list("galleries")]

# load all models from the database
new_models = 0
new_gallery = 0

# list of all subfolders in the input folder
galleries = [f.path for f in os.scandir(input_folder) if f.is_dir() ]
for gallery in tqdm.tqdm(galleries, desc="Scanning galleries"):
  if gallery in processed_galleries: continue
  # read and parse the data.json file from the gallery folder
  data_file = f"{gallery}/data.json"
  if not os.path.exists(data_file): continue

  data = json.load(open(data_file))
  gallery_models = data['models'].split(', ')
  gallery = model.Gallery(
    path = gallery,
    is_solo = len(gallery_models) == 1,
  )
  for model_name in gallery_models:
    existing_models = model.Model.objects(name=model_name)
    if existing_models.count() == 0:
      # create a new model
      new_model = model.Model(
        name = model_name,
        galleries = [gallery],
      )
      new_model.save()
      new_models += 1
    else:
      # update galleries list
      existing_model = existing_models.first()
      existing_model.galleries.append(gallery)
      existing_model.save()
  new_gallery += 1

print(f"Found {new_models} models")
print(f"Found {new_gallery} galleries")