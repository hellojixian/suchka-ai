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

processed_galleries = set()
existing_models = dict()
for m in tqdm.tqdm(model.Model.objects().all(), desc="Loading existing models"):
  for g in m.galleries:processed_galleries.add(g.path)
  existing_models[m.name] = m

# load all models from the database
new_models = 0
new_gallery = 0
skiped_galleries_no_json = 0
skiped_galleries_no_model_name = 0

# list of all subfolders in the input folder
galleries = set()
for f in os.scandir(input_folder): galleries.add(f.path)
for gallery in tqdm.tqdm(galleries, desc="Scanning galleries"):
  if gallery in processed_galleries: continue
  # read and parse the data.json file from the gallery folder
  data_file = f"{gallery}/data.json"
  if not os.path.exists(data_file): skiped_galleries_no_json+=1; continue

  data = json.load(open(data_file))
  if data['models'] == "": skiped_galleries_no_model_name+=1; continue
  gallery_models = data['models'].split(', ')
  gallery = model.Gallery(
    path = gallery,
    is_solo = len(gallery_models) == 1,
  )
  for model_name in gallery_models:
    if model_name == "": continue
    # check if the model_name already exists in existing_models
    if model_name not in existing_models:
      # create a new model
      new_model = model.Model(
        name = model_name,
        galleries = [gallery],
      )
      new_model.save()
      existing_models[model_name] = new_model
      new_models += 1
    else:
      # update galleries list
      existing_models[model_name]
      existing_models[model_name].galleries.append(gallery)
      existing_models[model_name].save()
  new_gallery += 1

print(f"Found {new_models} models")
print(f"Found {new_gallery} galleries")
print(f"Skipped {skiped_galleries_no_json} galleries - no data.json file")
print(f"Skipped {skiped_galleries_no_model_name} galleries - no model's namefile")