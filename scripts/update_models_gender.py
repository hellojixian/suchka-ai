#!/usr/bin/env python3
import os
import sys
import tqdm
import pickle
from dotenv import load_dotenv
load_dotenv()

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

import core.data_schema.model as model
from core.database import Database
db = Database()

# genders = ['male', 'female', 'shemale']
genders = ['male']

for gender in genders:
  name_file = os.path.join(os.environ['PROJECT_FACEDB_PATH'],f"{gender}_names.pickle")
  with open(name_file, 'rb') as f:
    names = pickle.load(f)

  for model_name in tqdm.tqdm(names, desc=f'Updating {gender} models'):
    model_data = model.Model.objects(name=model_name).first()
    if not model_data: continue
    model_data.gender = 'Male'
    model_data.save()
