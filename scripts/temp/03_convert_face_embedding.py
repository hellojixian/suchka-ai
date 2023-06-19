#!/usr/bin/env python3
# scan and load all galleries from the input folder

# create gallery objects and save into DB

import os
import sys
import tqdm
import pickle
import numpy as np
from copy import deepcopy
from dotenv import load_dotenv
load_dotenv()
import torch

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(project_root)

import core.data_model as model
from core.database import Database
db = Database()

face_root = os.getenv("PROJECT_FACEDB_PATH")

faces = model.Face.objects()
face_count = faces.count()
for _ in tqdm.tqdm(range(face_count), desc=f'Scan face folders'):
  face = next(faces)
  embedding_np = np.frombuffer(face.embedding_bin, dtype=np.float64)
  if embedding_np.shape[0] != 2622:
    # print(embedding_np.shape)
    if embedding_np.shape[0] == 1311: continue
    embedding_np = np.frombuffer(face.embedding_bin, dtype=np.float32)
  if embedding_np.shape[0] != 2622:
    print(embedding_np.shape)
    sys.exit(1)

  embedding_np32 = embedding_np.astype(np.float32)
  embedding_bin = embedding_np32.tobytes()
  # print(diff, len(embedding_bin), len(torch_bin))
  # # break
  # print(type(embedding_list), type(embedding_arr), type(embedding_bin), embedding_arr.shape)
  face.embedding_bin = embedding_bin
  face.save()
