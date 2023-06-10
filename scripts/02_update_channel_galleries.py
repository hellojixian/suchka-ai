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

channels = model.Channel.objects().all()
for channel in tqdm.tqdm(channels, desc="Update Channel => Galleries index"):
  channel.galleries = model.Gallery.objects(channels=channel.id)
  channel.save()
