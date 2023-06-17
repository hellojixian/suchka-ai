#!/usr/bin/env python3
# scan and load all galleries from the input folder

# create gallery objects and save into DB

import os
import sys
import json
import tqdm
from dotenv import load_dotenv
load_dotenv()

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

import core.data_model as model
from core.database import Database
db = Database()

project_folder = os.getenv("PROJECT_STORAGE_PATH")
data_folder = f"{project_folder}/{sys.argv[1]}"

processed_galleries = set()
existing_galleries = model.Gallery.objects()
for gallery in existing_galleries: processed_galleries.add(gallery.gid)
print(f"Found {len(processed_galleries)} galleries in the database")

def normalize_name(name):
  return " ".join([n.capitalize() for n in name.strip().split(' ')])

skiped_galleries_no_json = 0
# list of all subfolders in the input folder
galleries = set()
folders = [f for f in os.listdir(data_folder) if os.path.isdir(os.path.join(data_folder, f))]
for f in folders: galleries.add(f);
# sort galleries by name
galleries = sorted(galleries, key=lambda f: f)
for gallery in tqdm.tqdm(galleries, desc="Scanning galleries"):
  gid = gallery.split('/')[-1]
  if gid in processed_galleries: continue

  # read and parse the data.json file from the gallery folder
  data_file = f"{data_folder}/{gallery}/data.json"
  if not os.path.exists(data_file): skiped_galleries_no_json+=1; continue

  try:
    with open(data_file, 'r') as f:
      data = json.load(f)
  except:
    print(f"Failed to parse {data_file}")
    continue

  # fix data type for some fields
  if data['copyright'] is None:
    data['copyright'] = ""
    with open(data_file, 'w') as json_file:
      json_file.write(json.dumps(data))

  # !!! check if the gallery is already in the database
  #if ',' not in data['copyright']: continue

  gallery_path = os.path.abspath(f"{data_folder}/{gallery}")

  gallery_models = data['models'].split(', ') if data['models'] else []
  gallery_models = [normalize_name(m) for m in gallery_models]
  existing_models = model.Model.objects(name__in=gallery_models)
  existing_models = [m for m in existing_models]
  existing_model_names = [normalize_name(m.name) for m in existing_models]

  for model_name in gallery_models:
    if model_name not in existing_model_names:
      # create a new model
      new_model = model.Model(
        name = model_name,
        galleries = [],
        channels = [],
        tags = [],
        related_models = [],
      )
      new_model.save()
      existing_models.append(new_model)

  gallery_tags = data['tags'].split(', ') if data['tags'] else []
  existing_tags = model.Tag.objects(name__in=gallery_tags)
  existing_tags = [t for t in existing_tags]
  existing_tag_names = [m.name for m in existing_tags]
  for tag_name in gallery_tags:
    if tag_name not in existing_tag_names:
      new_tag = model.Tag(
        name = tag_name,
        models = [],
        galleries = [],
        channels = [],
      )
      new_tag.save()
      existing_tags.append(new_tag)

  gallery_channels = data['copyright'].split(', ') if data['copyright'] else []
  existing_channels = model.Channel.objects(name__in=gallery_channels)
  existing_channels = [c for c in existing_channels]
  existing_channel_names = [c.name for c in existing_channels]
  for channel_name in gallery_channels:
    if channel_name not in existing_channel_names:
      new_channel = model.Channel(
        name = channel_name,
        galleries = [],
        models = [],
        tags = []
      )
      new_channel.save()
      existing_channels.append(new_channel)

  gallery_obj = model.Gallery(
    gid = gid,
    url = data['url'],
    description = data['description'],
    source = data['source'],
    channels = existing_channels,
    tags = existing_tags,
    models = existing_models,
    path = gallery_path.replace(f"{project_folder}/", ""),
    is_solo = len(gallery_models) == 1,
  )
  # try:
  gallery_obj.save()

