#!/usr/bin/env python3
# scan and load all galleries from the input folder

# create gallery objects and save into DB

import os
import sys
import json
import tqdm
import pickle
from dotenv import load_dotenv
load_dotenv()

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

import core.data_schema.model as model
from core.database import Database
db = Database()

cached_index_root = f"{os.environ['PROJECT_STORAGE_PATH']}/cached_index"
if not os.path.exists(cached_index_root): os.mkdir(cached_index_root)

cached_tags = dict()
cached_tags_file = f"{cached_index_root}/cached_tags.pickle"
cache_tag_record = { 'galleries': set(), 'models': dict(), 'channels': dict() }

cached_channels = dict()
cached_channels_file = f"{cached_index_root}/cached_channels.pickle"
cached_channel_record = { 'children': set(), 'parent': None, 'models': dict(), 'galleries': set(), 'tags': dict() }

cached_models = dict()
cached_models_file = f"{cached_index_root}/cached_models.pickle"
cached_model_record = { 'channels': dict(), 'galleries': set(), 'models': dict(), 'tags': dict(),}

galleries = model.Gallery.objects()
for _ in tqdm.tqdm(range(galleries.count()), desc="Scan galleries from DB"):
  gallery = next(galleries).to_mongo().to_dict()
  gallery_id = gallery['_id']
  # process channels parent-child relationship
  if len(gallery['channels']) >= 2:
    parent_channel_id = gallery['channels'][0]
    if parent_channel_id not in cached_channels.keys():
      cached_channels[parent_channel_id] = cached_channel_record
    for i in range(1, len(gallery['channels'])):
      if parent_channel_id in cached_channels.keys():
        child_channel_id = gallery['channels'][i]
        if child_channel_id not in cached_channels[parent_channel_id]['children']:
          cached_channels[parent_channel_id] = cached_channel_record
        cached_channels[parent_channel_id]['children'].add(child_channel_id)
        if child_channel_id not in cached_channels.keys():
          cached_channels[child_channel_id] = cached_channel_record
        cached_channels[child_channel_id]['parent'] = parent_channel_id

  # process channels relationship
  for channel_id in gallery['channels']:
    if channel_id not in cached_channels.keys():
      cached_channels[channel_id] = cached_channel_record
    for model_id in gallery['models']:
      if model_id not in cached_channels[channel_id]['models'].keys():
        cached_channels[channel_id]['models'][model_id] = set()
      cached_channels[channel_id]['models'][model_id].add(gallery_id)
    for tag_id in gallery['tags']:
      if tag_id not in cached_channels[channel_id]['tags'].keys():
        cached_channels[channel_id]['tags'][tag_id] = set()
      cached_channels[channel_id]['tags'][tag_id].add(gallery_id)
    if gallery_id not in cached_channels[channel_id]['galleries']:
      cached_channels[channel_id]['galleries'].add(gallery_id)

  # process models relationship
  for model_id in gallery['models']:
    if model_id not in cached_models.keys():
      cached_models[model_id] = cached_model_record
    for channel_id in gallery['channels']:
      if channel_id not in cached_models[model_id]['channels'].keys():
        cached_models[model_id]['channels'][channel_id] = set()
      cached_models[model_id]['channels'][channel_id].add(gallery_id)
    for tag_id in gallery['tags']:
      if tag_id not in cached_models[model_id]['tags'].keys():
        cached_models[model_id]['tags'][tag_id] = set()
      cached_models[model_id]['tags'][tag_id].add(gallery_id)
    for model_model_id in gallery['models']:
      if model_model_id not in cached_models[model_id]['models'].keys():
        cached_models[model_id]['models'][model_model_id] = set()
      cached_models[model_id]['models'][model_model_id].add(gallery_id)
    if gallery_id not in cached_models[model_id]['galleries']:
      cached_models[model_id]['galleries'].add(gallery_id)

  # process tags relationship
  for tag_id in gallery['tags']:
    if tag_id not in cached_tags.keys():
      cached_tags[tag_id] = cache_tag_record
    for model_id in gallery['models']:
      if model_id not in cached_tags[tag_id]['models'].keys():
        cached_tags[tag_id]['models'][model_id] = set()
      cached_tags[tag_id]['models'][model_id].add(gallery_id)
    for channel_id in gallery['channels']:
      if channel_id not in cached_tags[tag_id]['channels'].keys():
        cached_tags[tag_id]['channels'][channel_id] = set()
      cached_tags[tag_id]['channels'][channel_id].add(gallery_id)
    if gallery_id not in cached_tags[tag_id]['galleries']:
      cached_tags[tag_id]['galleries'].add(gallery_id)

  # if _ > 10000: break

def convert_dict_to_galleries(key, data):
  return [{key: _key, 'galleries': len(galleries_ids)} for _key, galleries_ids in data.items()]

def get_human_readable_size(file_path):
    size_bytes = os.path.getsize(file_path)
    units = ["B", "KB", "MB", "GB", "TB"]

    size = size_bytes
    unit_index = 0
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    return f"{size:.2f} {units[unit_index]}"


print('Saving cached channels data', end=' ')
with open(cached_channels_file, 'wb') as f:
  pickle.dump(cached_channels, f)
print(f"\t size: {get_human_readable_size(cached_channels_file)}")

print('Saving cached tags data', end=' ')
with open(cached_tags_file, 'wb') as f:
  pickle.dump(cached_tags, f)
print(f"\t size: {get_human_readable_size(cached_tags_file)}")

print('Saving cached models data', end=' ')
with open(cached_models_file, 'wb') as f:
  pickle.dump(cached_models, f)
print(f"\t size: {get_human_readable_size(cached_channels_file)}")

# Get the pymongo connection from mongoengine connection
from pymongo import MongoClient
pymongo_client = MongoClient(os.environ.get('MONGODB_URI'))
pydb = pymongo_client.get_database()

for channel_id, channel in tqdm.tqdm(cached_channels.items(), desc="Update channels bulk operations"):
  pydb.model.update_one(
  {"filter": {"_id": channel_id}},
  {"$set": {
    # "galleries": list(channel["galleries"]),
    "tags": convert_dict_to_galleries("tag", channel["tags"]),
    "models": convert_dict_to_galleries("model", channel["models"]),
  }})
del cached_channels

for tag_id, tag in tqdm.tqdm(cached_tags.items(), desc="Update tags bulk operations"):
  pydb.tag.update_one(
  {"filter": {"_id": tag_id}},
  {"$set": {
    # "galleries": list(tag["galleries"]),
    "channels": convert_dict_to_galleries("channel", tag["channels"]),
    "models": convert_dict_to_galleries("model", tag["models"]),
  }})
del cached_tags


for model_id, model in tqdm.tqdm(cached_models.items(), desc="Update models bulk operations"):
  pydb.tag.update_one(
  {"filter": {"_id": model_id}},
  {"$set": {
    # "galleries": list(model["galleries"]),
    "channels": convert_dict_to_galleries("channel", model["channels"]),
    "tags": convert_dict_to_galleries("tag", model["tags"]),
    "models": convert_dict_to_galleries("model", model["models"]),
  }})
del cached_models
