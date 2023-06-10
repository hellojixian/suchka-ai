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

checked_channels = set()
galleries = model.Gallery.objects(__raw__={  '$expr': { '$gte': [{ '$size': '$channels' }, 2]} })
for gallery in tqdm.tqdm(galleries, desc="Update Channel's parent index"):
  for i in range(1, len(gallery.channels)):
    if gallery.channels[i].id in checked_channels: continue
    if gallery.channels[i] not in gallery.channels[0].children:
      gallery.channels[0].children.append(gallery.channels[i])
      # print("save new child")
      gallery.channels[0].save()
    if gallery.channels[i].parent != gallery.channels[0]:
      gallery.channels[i].parent = gallery.channels[0]
      # print("save new parent")
      gallery.channels[i].save()
    checked_channels.add(gallery.channels[i].id)
  for c in gallery.channels: del c
  del gallery.channels
del checked_channels
