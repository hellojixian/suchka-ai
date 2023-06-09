import os
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(project_root)

import numpy as np
import cv2
from core.data_model import Model, Face, GenderEnum
from core.face.batch_processor import process_batch
from core.face.gender import Gender

from mongoengine import NotUniqueError
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
load_dotenv()

storage_root = os.getenv("PROJECT_STORAGE_PATH")
facedb_root = os.getenv("PROJECT_FACEDB_PATH")
max_galleries = 30
group_face_threshold = 0.65

def gather_images(model:Model):
  # sort galleries by gallery models count ascending
  model_images = []
  image_gallery_mapping = dict()
  galleries = sorted(model.galleries, key=lambda g: g.is_solo)
  for i in range(len(galleries)):
    if i >= max_galleries: break
    gallery = model.galleries[i]
    gallery_path = os.path.join(storage_root, gallery.path)
    if not os.path.exists(gallery_path): continue
    images = [f'{gallery_path}/{f}' for f in os.listdir(gallery_path) if os.path.isfile(os.path.join(gallery_path, f)) and f.split('.')[-1].lower() == 'jpg']
    for image_path in images: image_gallery_mapping[image_path] = gallery.id
    model_images += images
  return model_images, image_gallery_mapping

def group_faces(model:Model, face_results:dict):
  face_dataset = dict()
  face_embeddings = dict()
  for image_path, faces in face_results.items():
    for i in range(len(faces)):
      face = faces[i]
      # print(face.keys())
      facial_gender = get_facial_gender([face])
      if model.gender:
        expected_gender = model.gender.value
        if model.gender is GenderEnum.SHEMALE: expected_gender = GenderEnum.FEMALE.value
        if facial_gender != expected_gender: continue
      face_dataset[f'{image_path}_face{i}'] = face
      face_embeddings[f'{image_path}_face{i}'] = face['embedding']
  grouped_faces = []
  visited = set()
  keys = list(face_embeddings.keys())
  data_matrix = np.array([list(embedding) for embedding in face_embeddings.values()])
  if len(keys) == 0: return None, None
  m = cosine_similarity(data_matrix)
  for i in range(len(m)):
    if i in visited: continue
    group = dict()
    group[keys[i]] = face_embeddings[keys[i]]
    for j in range(len(m)):
      if j in visited: continue
      if i == j: continue
      similarity = m[i][j]
      if similarity >= group_face_threshold:
        visited.add(i)
        visited.add(j)
        group[keys[j]] = face_embeddings[keys[j]]
    if len(group) > 1: grouped_faces.append(group)
  return grouped_faces, face_dataset

def find_common_faces(grouped_faces:dict, face_dataset:dict):
  if not grouped_faces: return []
  # find which group of faces contains the most galleries
  group_galleries = {}
  for group_id in range(len(grouped_faces)):
    if group_id not in group_galleries: group_galleries[group_id] = set()
    group = grouped_faces[group_id]
    for face_id, _ in group.items():
      group_galleries[group_id].add(face_dataset[face_id]['gallery_id'])
  # find the group with the most galleries
  max_group_id = max(group_galleries, key=lambda x: len(group_galleries[x]), default=None)
  if max_group_id is None: return []
  common_face_ids = grouped_faces[max_group_id].keys()
  common_faces = [face_dataset[face_id] for face_id in common_face_ids]
  return common_faces

def get_facial_gender(faces:list):
  if len(faces) == 0: return None
  gender_id = np.array([list(face['gender'].values()) for face in faces], dtype=float).mean(axis=0).argmax()
  return Gender.labels[gender_id]

def save_model_faces(model:Model, common_faces:list, pbar=None, pbar_prefix:str=None):
  model_folder = os.path.join(facedb_root, model.name)
  if not os.path.exists(model_folder): os.makedirs(model_folder)
  if pbar: pbar.set_description(f'{pbar_prefix} : Savining'.ljust(35))
  if pbar: pbar.reset(total=len(common_faces))

  for face_data in common_faces:
    try:
      filename = os.path.basename(face_data['image_path'])
      image_path = os.path.join(model_folder, filename)
      cv2.imwrite(image_path, face_data['cropped_face'])
      face = Face(
        name=model.name,
        filename=filename,
        source=face_data['image_path'].replace(storage_root, ''),
        embedding_bin=np.array(face_data['embedding']).astype(dtype=np.float32).tobytes(),
        gallery=face_data['gallery_id'],
        model=model.id,
      )
      face.save()
      model.faces.append(face)
      if pbar: pbar.update(1)
    except NotUniqueError as e: pass
    except Exception as e:
      print(e)
      continue
  facial_gender = get_facial_gender(common_faces)
  model.face_extracted = True
  model.facial_gender = facial_gender
  model.save()
  return

def process_model_faces(model:Model, pbar=None):
  model_images, image_gallery_mapping = gather_images(model)
  results = process_batch(images=model_images, device='gpu', threads=2, pbar=pbar, pbar_prefix=f'{model.name.rjust(20)}')
  for image_path, faces in results.items():
    for i in range(len(faces)):
      faces[i]['gallery_id'] = image_gallery_mapping[image_path]
      faces[i]['image_path'] = image_path

  grouped_faces, face_dataset = group_faces(model, results)
  common_faces = find_common_faces(grouped_faces, face_dataset)
  save_model_faces(model, common_faces, pbar=pbar, pbar_prefix=f'{model.name.rjust(20)}')
  return