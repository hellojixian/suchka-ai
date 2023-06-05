import os
import cv2
import logging
import tqdm
import sys
import numpy as np
import pandas as pd
import pickle
import shutil

# project_root = os.path.abspath(os.path.join(os.path.dirname('../')))
# sys.path.append(project_root)

from sklearn.metrics.pairwise import cosine_similarity
import core.data_schema.model as model

from deepface import DeepFace
from dotenv import load_dotenv
load_dotenv()

DEEPFACE_BACKEND = os.getenv("DEEPFACE_BACKEND")
DEEPFACE_MODEL = os.getenv("DEEPFACE_MODEL")

project_folder = os.getenv("PROJECT_STORAGE_PATH")
group_face_threshold = 0.65
common_face_threshold = 0.65
check_similarity_threshold = 0.65
confidence_threshold = 0.95
gender_threshold = 0.98
unknown_gender_threshold = 0.9
min_face_size = 50

def convert_dict_to_matrix(dictionary):
    keys = list(dictionary.keys())
    for i, key in enumerate(keys):
      values = dictionary[key]
      if type(values) == tuple: values = list(values)[0]
      dictionary[key] = values
    num_rows = len(dictionary)
    num_cols = max(len(values) for values in dictionary.values())
    matrix = np.zeros((num_rows, num_cols))
    for i, key in enumerate(keys):
      values = dictionary[key]
      matrix[i, :len(values)] = values
    return matrix

def crop_image(image_path, region, target_size = (224, 224)):
  image = cv2.imread(image_path)
  # Calculate the aspect ratio of the cropped region
  aspect_ratio = float(region['w']) / region['h']
  # Calculate the new width and height based on the target size and aspect ratio
  if aspect_ratio > 1:
    edge_length = region['w']
    x_offset = 0
    y_offset = (int)((region['w'] - region['h'])/ 2)
  else:
    edge_length = region['h']
    x_offset =  (int)((region['h'] - region['w'])/ 2)
    y_offset = 0

  crop_x = region['x'] - x_offset
  crop_w = region['x'] + x_offset + edge_length
  crop_y = region['y'] - y_offset
  crop_h = region['y'] + y_offset + edge_length

  # adjust the crop region to fit within the image boundaries
  if crop_x < 0:
    crop_w += np.abs(crop_x); crop_x = 0
  if crop_y < 0:
    crop_h += np.abs(crop_y); crop_y = 0
  if crop_w > image.shape[1]:
    crop_x -= crop_w - image.shape[1]
  if crop_h > image.shape[0]:
    crop_y -= crop_h - image.shape[0]

  # Crop the specified region
  cropped = image[crop_y:crop_h, crop_x:crop_w]
  # Resize the cropped region while maintaining the aspect ratio
  resized = cv2.resize(cropped, target_size, interpolation=cv2.INTER_AREA)
  return resized

def silence_tensorflow():
  """Silence every unnecessary warning from tensorflow."""
  logging.getLogger('tensorflow').setLevel(logging.ERROR)
  os.environ["KMP_AFFINITY"] = "noverbose"
  os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
  try:
    import tensorflow as tf
    tf.get_logger().setLevel('ERROR')
    tf.autograph.set_verbosity(3)
  except ModuleNotFoundError:
    pass

def check_similarity(embedding, existing_embeddings):
  embedding_matrix = convert_dict_to_matrix(existing_embeddings)
  similarity = np.mean(cosine_similarity([embedding], embedding_matrix))
  return similarity >= check_similarity_threshold

def save_common_face(data, gender_df, output_path, src_gallery_path):
  embeddings = dict()
  embeddings_file = f'{output_path}/embeddings.pickle'
  gender_file     = f'{output_path}/gender.pickle'
  final_gender_df = pd.DataFrame(columns=["Man", "Woman"])
  # moving files
  for f,v in data.items():
    filename = os.path.basename(f).split('_')[0]+'.jpg'
    shutil.copy(f, f'{output_path}/{filename}')
    embeddings[filename] = v
    final_gender_df.loc[filename] = gender_df.loc[f]
  # ceate embedding file
  with open(embeddings_file, 'wb') as f:
    f.write(pickle.dumps(embeddings))
  final_gender_df.to_pickle(gender_file)
  return

def cluster_embeddings(embeddings, threshold):
  groups = []
  data = embeddings
  visited = set()
  keys = list(data.keys())
  data_matrix = convert_dict_to_matrix(data)
  m = cosine_similarity(data_matrix)
  for i in range(len(m)):
    if i in visited: continue
    # print(i, keys[i].replace(' ','\ '))
    group = dict()
    group[keys[i]] = data[keys[i]]
    for j in range(len(m)):
      if j in visited: continue
      if i == j: continue
      similarity = m[i][j]
      if similarity >= threshold:
        visited.add(i)
        visited.add(j)
        group[keys[j]] = data[keys[j]]
        # print(j, similarity,keys[j].replace(' ','\ '))
    if len(group) > 1: groups.append(group)
  return groups

def detected_common_face(data, common_face_threshold):
  common_face = dict()
  pairs = dict()
  for gid in data.keys():
    other_galleries_gids = [g for g in data.keys() if g != gid]
    for fid in range(len(data[gid])):
      face_id = f'{gid}/{fid}'
      for gid2 in other_galleries_gids:
        for fid2 in range(len(data[gid2])):
          other_face_id = f'{gid2}/{fid2}'
          key = f'{face_id}-{other_face_id}'
          key2 = f'{other_face_id}-{face_id}'
          value = [gid,fid,gid2,fid2]
          if key not in pairs.keys() and key2 not in pairs.keys(): pairs[key] = value

  for key, value in pairs.items():
    common_face = dict()
    face_embeddings = list(data[value[0]][value[1]].values())
    face2_embeddings = list(data[value[2]][value[3]].values())
    similarity = np.mean(cosine_similarity(face_embeddings, face2_embeddings))
    if similarity >= common_face_threshold:
      common_face.update(data[value[0]][value[1]])
      common_face.update(data[value[2]][value[3]])
      break
  return common_face


def init_model_face_db(model_name, galleries, output_dir):
  """Initialize the face recognition model."""
  # create a temp folder to store the temp faces
  gallery_root = ""
  model_face_folder = f'{output_dir}/{model_name}'
  temp_folder = f'{model_face_folder}/temp'
  if not os.path.exists(model_face_folder): os.mkdir(model_face_folder)
  if not os.path.exists(temp_folder): os.mkdir(temp_folder)

  gender_df = pd.DataFrame(columns=["Man", "Woman"])
  model_data = model.Model.objects(name=model_name).first()
  detected = False
  grouped_faces_by_gallery = {}
  for gallery in galleries:
    gallery_faces = dict()
    gid = gallery.path.split('/')[-1]
    if gallery_root == "": gallery_root = gallery.path.replace(f'/{gid}', '')
    if not os.path.exists(f'{temp_folder}/{gid}'): os.mkdir(f'{temp_folder}/{gid}')
    # extract all faces from one gallery
    images = [f.path for f in os.scandir(f"{project_folder}/{gallery.path}") if f.name.lower().endswith(".jpg")]
    for image_path in tqdm.tqdm(images, desc=f'Extracting init faces from {gallery.path}'):
      output_file = f'{temp_folder}/{gid}/{os.path.basename(image_path).replace(".jpg", "")}_0.jpg'
      faces = DeepFace.extract_faces(img_path = image_path,
                                     enforce_detection = False,
                                     grayscale = False,
                                     align = True,
                                     detector_backend = DEEPFACE_BACKEND)
      face_id = 0
      for face in faces:
        output_file = f'{temp_folder}/{gid}/{os.path.basename(image_path).replace(".jpg", "")}_{face_id}.jpg'
        temp_file = f'{temp_folder}/temp.jpg'
        if face['confidence'] <= confidence_threshold: continue
        if face['facial_area']['w'] < min_face_size or face['facial_area']['h'] < min_face_size: continue
        cropped_face = crop_image(image_path, face['facial_area'])
        cv2.imwrite(temp_file, cropped_face)

        # print(f'{model_data.name} => {model_data.gender}')

        # filter out faces which the gender is not matched
        face_analysis = DeepFace.analyze(img_path = temp_file,
                                        actions=['gender'],
                                        enforce_detection=False,
                                        silent=True,
                                        align=True,
                                        detector_backend = DEEPFACE_BACKEND)

        if len(face_analysis) == 0: continue
        face_gender = face_analysis[0]['gender']
        if model_data.gender:
          if model_data.gender.lower() == 'male':
            if face_gender['Man'] < gender_threshold * 100:
              # print('not male - deleted')
              os.remove(temp_file)
              continue
            # else: print(face_gender['Man'], gender_threshold * 100)
          elif model_data.gender.lower() == 'female' or model_data.gender.lower() == 'shemale':
            if face_gender['Woman'] < gender_threshold * 100:
              os.remove(temp_file)
              continue
        else:
          max_gender = np.max([face_gender['Man'], face_gender['Woman']])
          if max_gender < unknown_gender_threshold * 100:
            os.remove(temp_file)
            continue

        face_embeddings = DeepFace.represent(img_path = temp_file,
                              enforce_detection=False,
                              align=True,
                              model_name=DEEPFACE_MODEL,
                              detector_backend = DEEPFACE_BACKEND)
        if len(face_embeddings) != 1:
          os.remove(temp_file)
          continue

        gender_df.loc[output_file] = pd.Series(face_gender, index=gender_df.columns)
        os.rename(temp_file, output_file)
        face_embedding = face_embeddings[0]
        gallery_faces[output_file] = face_embedding['embedding']
        face_id += 1

    # save cached embeddings file
    embedding_cache_file = f'{temp_folder}/{gid}/embeddings.pickle'
    with open(embedding_cache_file, 'wb') as f:
      f.write(pickle.dumps(gallery_faces))

    if len(gallery_faces) == 0: continue
    # group all faces by similarity of embeddings with threshold
    groupped_face = cluster_embeddings(gallery_faces, group_face_threshold)
    grouped_faces_by_gallery[gid] = groupped_face
    # find the common embedding so far
    common_face = detected_common_face(grouped_faces_by_gallery, common_face_threshold)
    if len(common_face) > 0:
      save_common_face(common_face, gender_df, model_face_folder, gallery_root)
      detected = True
      break
  if detected == False:
    # use the most elements in the group as common face
    gid = list(grouped_faces_by_gallery.keys())[0]
    grouped_face = grouped_faces_by_gallery[gid]
    most_elements = [len(grouped_face[id]) for id in range(len(grouped_face))]
    idx = most_elements.index(max(most_elements))
    common_face = grouped_face[idx]
    save_common_face(common_face, gender_df, model_face_folder, gallery_root)
  # delete temp folder
  shutil.rmtree(temp_folder)
