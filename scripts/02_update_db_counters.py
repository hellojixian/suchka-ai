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

models = model.Model.objects().all()
for model_obj in tqdm.tqdm(models, desc="Update Models => Galleries index"):
  model_obj.galleries = model.Gallery.objects(models=model_obj.id)
  model_obj.save()

tags = model.Tag.objects().all()
for tag in tqdm.tqdm(tags, desc="Update Tags => Galleries index"):
  tag.galleries = model.Gallery.objects(tags=tag.id)
  tag.save()

channels = model.Channel.objects().all()
for channel in tqdm.tqdm(channels, desc="Update Channel => Galleries index"):
  channel.galleries = model.Gallery.objects(channels=channel.id)
  channel.save()

for model_obj in tqdm.tqdm(models, desc="Update Models => Tags index"):
  model_tags = model.Tag.objects(models=model_obj.id)
  model_obj.tags = []
  for tag in model_tags:
    new_model_tag = model.ModelTag(
      tag = tag,
      count = len(model.Gallery.objects(tags=tag.id, models=model_obj.id))
    )
    model_obj.tags.append(new_model_tag)
  model_obj.save()

for model_obj in tqdm.tqdm(models, desc="Update Models => Channel index"):
  galleries = model.Gallery.objects(channel=model_obj.id)
  model_obj.channels = []
  for gallery in galleries:
    for channel in gallery.channels:
      if channel not in model_obj.channels:
        print(f"channel: {channel.name}")
        model_obj.channels.append(channel)
  print("Saving model")
  model_obj.save()

for tag in tqdm.tqdm(tags, desc="Update Tags => Models index"):
  tag_models = model.Model.objects(tags=tag.id)
  tag.models = []
  for model_obj in tag_models:
    new_tag_model = model_obj.TagModel(
      model = model_obj,
      galleries = len(model.Gallery.objects(tags=tag.id, models=model_obj.id))
    )
    tag.models.append(new_tag_model)
  tag.save()

for channel in tqdm.tqdm(channels, desc="Update Channel => Models, Tags index"):
  channel_models = model.Model.objects(channels=channel.id)
  channel.models = []
  for model_obj in channel_models:
    new_channel_model = model.ChannelModel(
      model = model_obj,
      galleries = len(model.Gallery.objects(channels=channel.id, models=model_obj.id))
    )
    channel.models.append(new_channel_model)

  channel_tags = model.Tag.objects(channels=channel.id)
  channel.tags = []
  for tag in channel_tags:
    new_channel_tag = model.ChanneTag(
      tag = tag,
      galleries = len(model.Gallery.objects(channels=channel.id, tags=tag.id))
    )
    channel.tags.append(new_channel_tag)
  channel.save()