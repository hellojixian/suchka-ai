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

import core.data_schema.model as model
from core.database import Database
db = Database()

project_folder = os.getenv("PROJECT_STORAGE_PATH")
data_folder = f"{project_folder}/{sys.argv[1]}"

processed_galleries = set()
existing_galleries = model.Gallery.objects()
for gallery in existing_galleries: processed_galleries.add(gallery.gid)

def normalize_name(name):
  return " ".join([n.capitalize() for n in name.strip().split(' ')])

skiped_galleries_no_json = 0
# list of all subfolders in the input folder
galleries = set()
for f in os.scandir(data_folder): galleries.add(f.path)
# sort galleries by name
galleries = sorted(galleries, key=lambda f: f.name)
for gallery in tqdm.tqdm(galleries, desc="Scanning galleries"):
  gid = gallery.split('/')[-1]
  if gid in processed_galleries:continue

  # read and parse the data.json file from the gallery folder
  data_file = f"{gallery}/data.json"
  if not os.path.exists(data_file): skiped_galleries_no_json+=1; continue

  try:
    data = json.load(open(data_file))
  except:
    print(f"Failed to parse {data_file}")
    continue

  gallery_models = data['models'].split(', ') if data['models'] else []
  existing_models = model.Model.objects(name__in=gallery_models)
  existing_models = [m for m in existing_models]
  existing_model_names = [m.name for m in existing_models]
  for model_name in gallery_models:
    if model_name not in existing_model_names:
      # create a new model
      new_model = model.Model(
        name = normalize_name(model_name),
        galleries = [],
        channels = [],
        tags = [],
      )
      new_model.save()
      existing_models.append(new_model)

  gallery_tags = data['tags'].split(', ') if data['tags'] else []
  existing_tags = model.Tag.objects(name__in=gallery_models)
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
    path = gallery.replace(f"{project_folder}/", ""),
    is_solo = len(gallery_models) == 1,
  )
  # try:
  gallery_obj.save()


models = model.Model.objects().all()
for model_obj in tqdm.tqdm(models, desc="Update Models => Galleries index"):
  model_obj.galleries = model.Gallery.objects(models__name=model_obj.name)
  model_obj.save()

tags = model.Tag.objects().all()
for tag in tqdm.tqdm(tags, desc="Update Tags => Galleries index"):
  tag.galleries = model.Tag.objects(tags__name=tag.name)
  tag.save()

channels = model.Channel.objects().all()
for channel in tqdm.tqdm(channels, desc="Update Channel => Galleries index"):
  channel.galleries = model.Channel.objects(channel=channel.name)
  channel.save()

for model_obj in tqdm.tqdm(models, desc="Update Models => Tags index"):
  model_tags = model.Tag.objects(models__name=model_obj.name)
  model_obj.tags = []
  for tag in model_tags:
    new_model_tag = model.ModelTag(
      tag = tag,
      count = len(model.Gallery.objects(tags__name=tag.name, models__name=model_obj.name))
    )
    model_obj.tags.append(new_model_tag)
  model_obj.save()

for model_obj in tqdm.tqdm(models, desc="Update Models => Channel index"):
  galleries = model.Gallery.objects(channel=model_obj.name)
  model_obj.channels = []
  for gallery in galleries:
    channel = model.Channel.objects(name=gallery.channel)
    if channel.name not in [c.name for c in model_obj.channels]:
      model_obj.channels.append(channel)
  model_obj.save()

for tag in tqdm.tqdm(tags, desc="Update Tags => Models index"):
  tag_models = model.Model.objects(tags_name=tag.name)
  tag.models = []
  for model_obj in tag_models:
    new_tag_model = model_obj.TagModel(
      model = model_obj,
      count = len(model.Gallery.objects(tags__name=tag.name, models__name=model_obj.name))
    )
    tag.models.append(new_tag_model)
  tag.save()

for channel in tqdm.tqdm(channels, desc="Update Channel => Models, Tags index"):
  channel_models = model.Model.objects(channel=channel.name)
  channel.models = []
  for model_obj in channel_models:
    new_channel_model = model.ChannelModel(
      model = model_obj,
      count = len(model.Gallery.objects(channel=channel.name, models__name=model_obj.name))
    )
    channel.models.append(new_channel_model)

  channel_tags = model.Tag.objects(channel=channel.name)
  channel.tags = []
  for tag in channel_tags:
    new_channel_tag = model.ChanneTag(
      tag = tag,
      count = len(model.Gallery.objects(channel=channel.name, tags__name=tag.name))
    )
    channel.models.append(new_channel_model)
  channel.save()