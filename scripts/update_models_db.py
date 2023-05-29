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

# load all models from the database
new_models = {}

# list of all subfolders in the input folder
subfolders = [f.path for f in os.scandir(input_folder) if f.is_dir() ]
for gallery in tqdm.tqdm(subfolders, desc="Scanning galleries"):
  # read and parse the data.json file from the gallery folder
  data_file = f"{gallery}/data.json"
  if not os.path.exists(data_file): continue
  data = json.load(open(data_file))
  gallery_models = data['models'].split(', ')
  for model_name in gallery_models:
    if model_name not in new_models.keys():
      new_models[model_name] = {
        "name": model_name,
        "galleries": {},
      }
    if data['id'] not in new_models[model_name]['galleries'].keys():
      new_models[model_name]['galleries'][data['id']] = {
        "path": gallery,
        "is_solo": len(gallery_models) == 1,
      }

# print(json.dumps(new_models, indent=2))
print(f"Found {len(new_models)} models")

# fetch all models from the database
existing_models = model.Model.objects()

saved_models = []
for model_name in tqdm.tqdm(new_models.keys(), desc="Saving models"):
  # check if model exists in existing_models list, if not create a new model
  if len([m for m in existing_models if m.name == model_name]) == 0 and\
    len([m for m in saved_models if m.name == model_name]) == 0:
    # create a new model
    new_model = model.Model(
      name = model_name,
      galleries = [],
    )
    # add galleries to the model
    for gallery_id in new_models[model_name]['galleries'].keys():
      new_gallery = model.Gallery(
        path = new_models[model_name]['galleries'][gallery_id]['path'],
        is_solo = new_models[model_name]['galleries'][gallery_id]['is_solo'],
      )
      new_model.galleries.append(new_gallery)
    # save the model
    new_model.save()
    saved_models.append(new_model)
  else:
    # update galleries list
    # check saved_models first and then existing_models
    if len([m for m in saved_models if m.name == model_name]) > 0:
      existing_model = [m for m in saved_models if m.name == model_name][0]
    else:
      existing_model = [m for m in existing_models if m.name == model_name][0]

    need_save = False
    existing_gallery_paths = [g.path for g in existing_model.galleries]
    for gallery_id in new_models[model_name]['galleries'].keys():
      if new_models[model_name]['galleries'][gallery_id]['path'] not in existing_gallery_paths:
        new_gallery = model.Gallery(
          path = new_models[model_name]['galleries'][gallery_id]['path'],
          is_solo = new_models[model_name]['galleries'][gallery_id]['is_solo'],
        )
        existing_model.galleries.append(new_gallery)
        need_save = True
    if need_save: existing_model.save(validate=True)
print(f"Saved {len(saved_models)} new models")