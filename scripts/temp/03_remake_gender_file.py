#!/usr/bin/env python3
# scan and load all galleries from the input folder

# create gallery objects and save into DB

import os
import sys
import tqdm
import pickle
import pandas as pd
from copy import deepcopy
from dotenv import load_dotenv
load_dotenv()

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(project_root)

from deepface import DeepFace
import core.data_model as model
from core.database import Database
db = Database()

face_root = os.getenv("PROJECT_FACEDB_PATH")
DEEPFACE_BACKEND = os.getenv("DEEPFACE_BACKEND")
# faces = model.Face.objects()
# for _ in tqdm.tqdm(range(faces.count()), desc=f'Scan face folders'):
#   face = next(faces)
#   if not os.path.exists(face.path):
#     print(face.path)




#scan all folders in the face_root
# processed = 0
face_folders = [f for f in os.listdir(face_root) if os.path.isdir(os.path.join(face_root, f))]

for model_name in tqdm.tqdm(face_folders, desc=f'Scan face folders'):
  gender_file = f"{face_root}/{model_name}/gender.pickle"
  if not os.path.exists(gender_file):
    gender_df = pd.DataFrame(columns=["Man", "Woman"])
    print(f'gender file not found for {model_name}')
    for image in os.listdir(f"{face_root}/{model_name}"):
      # if image is not jpg file then continue
      if image.split('.')[-1].lower() != 'jpg': continue
      image_path = f"{face_root}/{model_name}/{image}"
      face_analysis = DeepFace.analyze(img_path = image_path,
                                        actions=['gender'],
                                        enforce_detection=False,
                                        silent=True,
                                        align=True,
                                        detector_backend = DEEPFACE_BACKEND)
      face_gender = face_analysis[0]['gender']
      gender_df.loc[os.path.basename(image_path)] = pd.Series(face_gender, index=gender_df.columns)
    gender_df.to_pickle(gender_file)
    # print(gender_df)

  # read gender file
  gender_df = pd.read_pickle(gender_file)
  gender_mean = gender_df.mean()

  model_obj = model.Model.objects(name=model_name).first()
  model_obj.facial_gender = model.GenderEnum.MALE if gender_mean['Man'] > gender_mean['Woman'] else model.GenderEnum.FEMALE
  model_obj.save()
  # break

