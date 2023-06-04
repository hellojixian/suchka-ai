#!/usr/bin/env python3
import os
import sys
import json
import tqdm
import cv2
import pickle
import gc
import keras.backend as K

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from core.face_processor import crop_image, silence_tensorflow,\
            init_model_face_db, check_similarity

silence_tensorflow()

from deepface import DeepFace
import deepface.detectors.FaceDetector as fd
from dotenv import load_dotenv
load_dotenv()

import core.data_schema.model as model
from core.database import Database

db = Database()

faces_dir = "output/faces"
output_dir = f'{project_root}/{faces_dir}'
confidence_threshold = 0.95
min_face_size = 60

model_faces = dict()
DEEPFACE_BACKEND = os.getenv("DEEPFACE_BACKEND")
DEEPFACE_MODEL = os.getenv("DEEPFACE_MODEL")

# Keras model has memory leak issue
# https://github.com/serengil/deepface/issues/697
cfg = K.tf.compat.v1.ConfigProto()
cfg.gpu_options.allow_growth = True
K.set_session(K.tf.compat.v1.Session(config=cfg))

def process_galleries(galleries,model_name):
  model_embeddings = []
  model_embedding_file = f'{output_dir}/{model_name}/embeddings.pickle'
  with open(model_embedding_file, 'rb') as file:
    model_embeddings = pickle.load(file)

  model_face_folder = f'{output_dir}/{model_name}'
  processed_log = f"{model_face_folder}/processed.log"
  processed_log_set = set()
  if not os.path.exists(model_face_folder): os.mkdir(model_face_folder)
  if os.path.exists(processed_log):
    with open(processed_log, 'rb') as file:
      processed_log_set = pickle.load(file)

  for gallery in galleries:
    images = [f.path for f in os.scandir(gallery.path) if f.name.lower().endswith(".jpg")]
    for image_path in tqdm.tqdm(images, desc=f'Extracting faces from {gallery.path}'):
      process_image(image_path,model_name, model_embeddings, processed_log_set)
  yield model_name


def process_image(image_path,model_name, model_embeddings, processed_log_set):
  embedding_file = f'{output_dir}/{model_name}/embeddings.pickle'
  need_save = False
  model_face_folder = f'{output_dir}/{model_name}'
  output_file = f"{model_face_folder}/{os.path.basename(image_path)}"
  output_file_key = f"{faces_dir}/{model_name}/{os.path.basename(image_path)}"
  processed_log = f"{model_face_folder}/processed.log"

  # if the face is already extracted, skip it
  if image_path in processed_log_set:
    # print('skipping - already processed', image_path)
    return
  else:
    processed_log_set.add(image_path)
    with open(processed_log, 'wb') as file:
      pickle.dump(processed_log_set, file)

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
    cv2.imwrite(output_file, cropped_face)
    # save the face embedding in the database
    face_embeddings = DeepFace.represent(img_path = output_file,
                            enforce_detection=False,
                            align=True,
                            model_name=DEEPFACE_MODEL,
                            detector_backend = DEEPFACE_BACKEND)
    if len(face_embeddings) == 0:return
    if not check_similarity(face_embeddings[0]['embedding'], model_embeddings): return
    # check if face is similar to other faces in the model
    model_data = model.Model.objects(name = model_name).first()
    model_data.faces.append(model.Face(path=output_file_key, source=image_path))
    model_embeddings[image_path] = face_embeddings[0]['embedding'],
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


if __name__ == '__main__':
  if not os.path.exists(output_dir): os.makedirs(output_dir)

  for m in tqdm.tqdm(model.Model.objects().all(), desc="Loading existing models"):
    # sort the galleries by is_solo
    sorted_galleries = sorted(m.galleries, key=lambda x: x["is_solo"], reverse=True)
    if len(sorted_galleries) >= 10: sorted_galleries = sorted_galleries[:10]
    model_faces[m.name] = sorted_galleries

  for model_name in tqdm.tqdm(model_faces.keys(), desc="Extracting models face"):
    if not " " in model_name: continue
    embedding_file = f'{output_dir}/{model_name}/embeddings.pickle'

    if not os.path.exists(embedding_file):
      # initalize the embedding files for the model
      init_model_face_db(model_name, model_faces[model_name], output_dir)

    for res in process_galleries(model_faces[model_name], model_name):
      pass
