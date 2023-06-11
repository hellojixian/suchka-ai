#!/usr/bin/env python3
# scan and load all galleries from the input folder

# create gallery objects and save into DB

import os
import sys
import tqdm
import pickle
from copy import deepcopy
from dotenv import load_dotenv
load_dotenv()

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

import core.data_schema.model as model
from core.database import Database
db = Database()

face_root = os.getenv("PROJECT_FACEDB_PATH")

# faces = model.Face.objects()
# for _ in tqdm.tqdm(range(faces.count()), desc=f'Scan face folders'):
#   face = next(faces)
#   if not os.path.exists(face.path):
#     print(face.path)




#scan all folders in the face_root
# processed = 0
# face_folders = [f for f in os.listdir(face_root) if os.path.isdir(os.path.join(face_root, f))]

# for model_name in tqdm.tqdm(face_folders, desc=f'Scan face folders'):
#   images = [f for f in os.listdir(f"{face_root}/{model_name}") if os.path.isfile(os.path.join(f"{face_root}/{model_name}", f))]
#   for image in images:
#     # if image is not jpg file then continue
#     if image.split('.')[-1].lower() != 'jpg': continue
#     processed += 1
#     filename = os.path.basename(image)
#     if model.Face.objects(name=model_name, filename=filename).count() == 0:
#       image_path = f"{face_root}/{model_name}/{image}"
#       os.remove(image_path)
#       print(f"{model_name} Removed {image_path}")
# print(f'Processed {processed} images')