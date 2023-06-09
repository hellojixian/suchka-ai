#!/usr/bin/env python3
import os
import sys
import tqdm
import pickle
import numpy as np
from dotenv import load_dotenv
load_dotenv()

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

import core.data_model as model
from core.database import Database
db = Database()

name_file = os.path.join(os.environ['PROJECT_FACEDB_PATH'], "gender_names.pickle")
with open(name_file, 'rb') as f:
  names = pickle.load(f)

records = 0
genders = sorted(names.keys(), key=lambda gender: len(names[gender]), reverse=False)
for gender in genders:
  r = len(names[gender])
  records += r
  print(f"{gender} => {r} records")
print(f"total {records} records loaded")

for gender in genders:
  for model_name in tqdm.tqdm(names[gender], desc=f'Updating {gender} models'):
    model_data = model.Model.objects(name=model_name).first()
    if not model_data: continue
    model_data.gender = gender
    model_data.save()
