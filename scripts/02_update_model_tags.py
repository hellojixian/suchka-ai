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
for model_obj in tqdm.tqdm(models, desc="Update Models => Tags index"):
  model_tags = model.Tag.objects(models=model_obj.id)
  print(model_obj.id, model_tags)
  model_obj.tags = []
  for tag in model_tags:
    new_model_tag = model.ModelTag(
      tag = tag,
      count = len(model.Gallery.objects(tags=tag.id, models=model_obj.id))
    )
    model_obj.tags.append(new_model_tag)
  model_obj.save()
