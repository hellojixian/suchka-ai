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

import core.data_schema.model as model
from core.database import Database
db = Database()

face_root = os.getenv("PROJECT_FACEDB_PATH")

faces = model.Face.objects()
for _ in tqdm.tqdm(range(faces.count()), desc=f'Scan face folders'):
  face = next(faces)
  embedding_fp32 = np.frombuffer(face.embedding_bin, dtype=np.float32)
  print(embedding_fp32.shape)
  # embedding_fp32 = embedding_fp64.astype(np.float32)
  # print(embedding_fp32.shape, embedding_fp64.shape)

  # print(np.sum(embedding_fp64 - embedding_fp32))
  embedding_bin = embedding_fp32.tobytes()
  print(len(embedding_bin))
  break
  # print(type(embedding_list), type(embedding_arr), type(embedding_bin), embedding_arr.shape)
  # face.embedding_bin = embedding_bin
  # face.save()
