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
  channels = gallery.channels
  for i in range(1, len(channels)):
    if channels[i].id in checked_channels: continue
    if channels[i] not in channels[0].children:
      channels[0].children.append(channels[i])
      # print("save new child")
      channels[0].save()
    if channels[i].parent != channels[0]:
      channels[i].parent = channels[0]
      # print("save new parent")
      channels[i].save()
    checked_channels.add(channels[i].id)
del checked_channels
