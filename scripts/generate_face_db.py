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

def process_galleries(galleries,model_name):
  model_embeddings = dict()
  model_embedding_file = f'{output_dir}/{model_name}/embeddings.pickle'
  if os.path.exists(model_embedding_file):
    with open(model_embedding_file, 'rb') as file:
      model_embeddings = pickle.load(file)

  model_face_folder = f'{output_dir}/{model_name}'
  processed_log = f"{model_face_folder}/processed.log"
  processed_log_set = set()
  if not os.path.exists(model_face_folder): os.mkdir(model_face_folder)
  if os.path.exists(processed_log):
    with open(processed_log, 'rb') as file:
      processed_log_set = pickle.load(file)

  model_data = model.Model.objects(name = model_name).first()
  gender_df = pd.DataFrame(columns=["Man", "Woman"])
  if not model_data.gender:
    gender_file = f'{model_face_folder}/gender.pickle'
    # patching gender
    if os.path.exists(gender_file):
      gender_df = pd.read_pickle(gender_file)
      gender_mean = gender_df.mean()
      model_data.gender = 'male' if gender_mean['Man'] > gender_mean['Woman'] else 'female'

  for gallery in galleries:
    images = [f.path for f in os.scandir(f"{project_folder}/{gallery.path}") if f.name.lower().endswith(".jpg")]
    for image_path in tqdm.tqdm(images, desc=f'Extracting faces from {gallery.path}'):
      if image_path in processed_log_set: continue

      processed_log_set.add(image_path)
      with open(processed_log, 'wb') as file:
        pickle.dump(processed_log_set, file)

      process_image(image_path, model_name, model_data,  model_embeddings, gender_df)
  yield model_name


def process_image(image_path,model_name, model_data, model_embeddings, gender_df):
  embedding_file = f'{output_dir}/{model_name}/embeddings.pickle'
  need_save = False
  model_face_folder = f'{output_dir}/{model_name}'
  output_file = f"{model_face_folder}/{os.path.basename(image_path)}"
  temp_file = f"{model_face_folder}/temp.jpg"
  gender_file = f'{model_face_folder}/gender.pickle'
  output_file_key = f"{model_name}/{os.path.basename(image_path)}"
  # if the face is already extracted, skip it
  faces = DeepFace.extract_faces(img_path = image_path,
                                  enforce_detection = False,
                                  grayscale = False,
                                  align = False,
                                  detector_backend = DEEPFACE_BACKEND)
  K.clear_session()
  gc.collect()

  # extract the face embedding
  # print(f'Extracted {len(faces)} faces from {image_path}')
  # usually when multiple faces are detected, it's a false positive and quality will be bad
  if len(faces) > 1: return
  for face in faces:
    if face['confidence'] <= confidence_threshold:
      return

    # ignore faces that are too small
    if face['facial_area']['w'] < min_face_size or face['facial_area']['h'] < min_face_size:
      return
    # crop the face from the image
    try:
      cropped_face = crop_image(image_path, face['facial_area'])
    except:
      return

    # save the face in the output folder
    cv2.imwrite(temp_file, cropped_face)

    # filter out faces which the gender is not matched
    face_analysis = DeepFace.analyze(img_path = temp_file,
                                      actions=['gender'],
                                      enforce_detection=False,
                                      silent=True,
                                      align=True,
                                      detector_backend = DEEPFACE_BACKEND)

    if len(face_analysis) == 0:return
    face_gender = face_analysis[0]['gender']
    if model_data.gender:
      if model_data.gender.lower() == 'male':
        if face_gender['Man'] < gender_threshold * 100:
          os.remove(temp_file)
          return
      elif model_data.gender.lower() == 'female' or model_data.gender.lower() == 'shemale':
        if face_gender['Woman'] < gender_threshold * 100:
          os.remove(temp_file)
          return
    else:
      max_gender = np.max([face_gender['Man'], face_gender['Woman']])
      if max_gender < unknown_gender_threshold * 100:
        os.remove(temp_file)
        return

    # save the face embedding in the database
    face_embeddings = DeepFace.represent(img_path = temp_file,
                            enforce_detection=False,
                            align=True,
                            model_name=DEEPFACE_MODEL,
                            detector_backend = DEEPFACE_BACKEND)
    if len(face_embeddings) == 0:
      os.remove(temp_file)
      return
    # check if face is similar to other faces in the model
    if len(model_embeddings) > 0:
      if not check_similarity(face_embeddings[0]['embedding'], model_embeddings):
        os.remove(temp_file)
        return

    gender_df.loc[os.path.basename(image_path)] = pd.Series(face_gender, index=gender_df.columns)
    gender_df.to_pickle(gender_file)
    os.rename(temp_file, output_file)
    model_data.faces.append(model.Face(path=output_file_key, source=image_path))
    model_embeddings[os.path.basename(image_path)] = face_embeddings[0]['embedding'],
    need_save = True

  if need_save:
    # save the model to the database
    model_data.save()
    # save the embeddings to the file
    with open(embedding_file, 'wb') as file:
      pickle.dump(model_embeddings, file)

  faces = None
  face_embeddings = None
  return

bad_names = ['Add To Favorites']
test_model = None
# test_model = 'James Deen'
# test_model = 'Ryan Madison'
# test_model = 'Sean Michaels'
# test_model = 'Lew Rubens'
# test_model = 'Ms Panther'
# test_model = 'Nicole Pitty'

def signal_handler(signal, frame):
    print("Ctrl+C pressed. Exiting gracefully...")
    print(f"release lock_file: {lock_file}")
    if os.path.exists(lock_file): os.remove(lock_file)
    sys.exit(0)


lock_file = None
if __name__ == '__main__':
  # Register the signal handler for SIGINT
  signal.signal(signal.SIGINT, signal_handler)

  if not os.path.exists(output_dir): os.makedirs(output_dir)

  for m in tqdm.tqdm(model.Model.objects().all(), desc="Loading existing models"):
    # sort the galleries by is_solo
    if test_model and m.name != test_model: continue
    sorted_galleries = sorted(m.galleries, key=lambda x: x["is_solo"], reverse=True)
    model_faces[m.name] = sorted_galleries

  # sort the model_names by number of galleries
  model_names = sorted(model_faces.keys(), key=lambda x: len(model_faces[x]), reverse=True)

  for model_name in tqdm.tqdm(model_names, desc="Extracting models face"):
    # filter out models with no space in the name and bad names
    if not " " in model_name: continue
    if model_name in bad_names: continue

    galleries = model_faces[model_name]
    if len(galleries) >= max_galleries_per_model: galleries = galleries[:max_galleries_per_model]
    # if len(model_faces[model_name]) <= 4: continue
    embedding_file = f'{output_dir}/{model_name}/embeddings.pickle'
    model_face_folder = f'{output_dir}/{model_name}'
    if not os.path.exists(model_face_folder): os.mkdir(model_face_folder)

    lock_file = f'{model_face_folder}/.lock'
    if os.path.exists(lock_file):
      print(f'Lock file exists for {model_name}')
      continue

    # add resource lock
    with open(lock_file, 'w') as f:
      f.write('')

    if not os.path.exists(embedding_file):
      # initalize the embedding files for the model
      init_model_face_db(model_name, galleries, output_dir)

    for res in process_galleries(galleries, model_name):
      pass

    # remove resource lock
    if os.path.exists(lock_file): os.remove(lock_file)
