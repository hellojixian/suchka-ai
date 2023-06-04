#!/usr/bin/env python3
import os
import sys
import json
import tqdm
import cv2
import pickle
import gc
import numpy as np
import pandas as pd
import keras.backend as K
import shutil


project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from core.face_processor import crop_image, silence_tensorflow,\
            init_model_face_db, check_similarity

silence_tensorflow()

from deepface import DeepFace
from dotenv import load_dotenv
load_dotenv()

import core.data_schema.model as model
from core.database import Database

db = Database()

project_folder = os.getenv("PROJECT_STORAGE_PATH")
faces_dir = os.getenv("PROJECT_FACEDB_PATH")

DEEPFACE_BACKEND = os.getenv("DEEPFACE_BACKEND")

if __name__ == '__main__':
  # list all subfolders in faces_dir
  models = [f.path for f in os.scandir(faces_dir) if f.is_dir() ]
  for model_name in models:
    data_file = f'{model_name}/embeddings.pickle'
    if not os.path.exists(data_file): continue
    with open(data_file, 'rb') as f:
      face_embeddings = pickle.load(f)

    keys = list(face_embeddings.keys())
    for k in keys:
      if k != os.path.basename(k):
        # convert the key to the basename
        face_embeddings[os.path.basename(k)] = list(face_embeddings[k]).copy()
        del face_embeddings[k]

    with open(data_file, 'wb') as f:
      f.write(pickle.dumps(face_embeddings))
    # print(face_embeddings.keys())
    print(model_name)
    print('------------------')
