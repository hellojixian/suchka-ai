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
import signal

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

output_dir = faces_dir
confidence_threshold = 0.95
gender_threshold = 0.98
unknown_gender_threshold = 0.9
min_face_size = 60
max_galleries_per_model = 15

model_faces = dict()
DEEPFACE_BACKEND = os.getenv("DEEPFACE_BACKEND")
DEEPFACE_MODEL = os.getenv("DEEPFACE_MODEL")

# Keras model has memory leak issue
# https://github.com/serengil/deepface/issues/697
cfg = K.tf.compat.v1.ConfigProto()
cfg.gpu_options.allow_growth = True
K.set_session(K.tf.compat.v1.Session(config=cfg))


lock_file = None
if __name__ == '__main__':
  # Register the signal handler for SIGINT

  if not os.path.exists(output_dir): os.makedirs(output_dir)


for m in tqdm.tqdm(model.Model.objects().all(), desc="Loading existing models"):
  # sort the galleries by is_solo
  sorted_galleries = sorted(m.galleries, key=lambda x: x["is_solo"], reverse=True)
  if len(sorted_galleries) >= max_galleries_per_model: sorted_galleries = sorted_galleries[:max_galleries_per_model]
  model_faces[m.name] = sorted_galleries

# sort the model_names by number of galleries
model_names = sorted(model_faces.keys(), key=lambda x: len(model_faces[x]), reverse=True)

for model_name in tqdm.tqdm(model_names, desc="Extracting models face"):
  print(model_name)





