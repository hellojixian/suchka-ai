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
  del model_obj.galleries
