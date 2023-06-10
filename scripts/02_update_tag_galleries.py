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

tags = model.Tag.objects().all()
for tag in tqdm.tqdm(tags, desc="Update Tags => Galleries index"):
  tag.galleries = model.Gallery.objects(tags=tag.id)
  # print(len(tag.galleries))
  tag.save()
  del tag.galleries
