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

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(project_root)

import core.data_model as model
from core.database import Database
db = Database()

face_root = os.getenv("PROJECT_FACEDB_PATH")

processed = 0
#scan all folders in the face_root
face_folders = [f for f in os.listdir(face_root) if os.path.isdir(os.path.join(face_root, f))]

for model_name in tqdm.tqdm(face_folders, desc=f'Scan face folders'):
  processed += 1
  # if processed < 1313: continue
  embedding_file = f"{face_root}/{model_name}/embeddings.pickle"
  if not os.path.exists(embedding_file): continue
  with open(embedding_file, 'rb') as f:
    embeddings = pickle.load(f)

  processlog_file = f"{face_root}/{model_name}/processed.log"
  with open(processlog_file, 'rb') as f:
    processlog = pickle.load(f)
  model_obj = model.Model.objects(name=model_name).first()
  model_faces = set()
  model_dict = model_obj.to_mongo().to_dict()
  if model_dict['faces'] and type(model_dict['faces'][0]) != dict:
    model_faces = model_obj.faces

  found_new_faces = False
  for filename, embedding in embeddings.items():
    if type(embedding) == tuple:
      embedding = list(embedding)[0]

    # print(len(embedding), type(embedding))
    found = False
    for file_path in processlog:
      if os.path.basename(file_path) == filename:
        gid = file_path.split('/')[-2]
        gallery = model.Gallery.objects(gid=gid).first()
        source = "/".join(file_path.split('/')[-3:])
        if model.Face.objects(name=model_name, source=source).count() == 0:
          face = model.Face(
            name  = model_name,
            model= model_obj.id,
            filename = filename,
            source = source,
            gallery = gallery.id,
            embedding = embedding,
          )
          found = True
          found_new_faces = True
          face.save()
          model_faces.add(face.id)
          break
        else:
          found = True
          break
    if not found:
      print(model_name, filename)

  if found_new_faces:
    model_obj.faces = list(model_faces)
    model_obj.save()
  # print(model_name, filename)