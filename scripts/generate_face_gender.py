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

import core.data_model as model
from core.database import Database

db = Database()

project_folder = os.getenv("PROJECT_STORAGE_PATH")
faces_dir = os.getenv("PROJECT_FACEDB_PATH")

DEEPFACE_BACKEND = os.getenv("DEEPFACE_BACKEND")

if __name__ == '__main__':
  # list all subfolders in faces_dir
  models = [f.path for f in os.scandir(faces_dir) if f.is_dir() ]
  for model_name in models:
    gender_file = f'{model_name}/gender.pickle'
    dataset = dict()
    # list all jpg files in model_name folder
    model_faces = [f.path for f in os.scandir(model_name) if f.is_file() and f.name.endswith('.jpg')]
    for face_file in tqdm.tqdm(model_faces, desc=f'Processing {model_name}'):
      face_analysis = DeepFace.analyze(img_path = face_file,
                                       actions=['gender'],
                                       enforce_detection=False,
                                       silent=True,
                                       align=True,
                                       detector_backend = DEEPFACE_BACKEND)
      if len(face_analysis) == 0: continue
      face_gender = face_analysis[0]['gender']
      dataset[os.path.basename(face_file)] = face_gender
    gender_df = pd.DataFrame(dataset).T
    gender_df.to_pickle(gender_file)
    print(model_name)
    print(gender_df)


