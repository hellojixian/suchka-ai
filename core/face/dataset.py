import os
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(project_root)

from core.face.vectorizer import FaceVectorizer
from torch.utils.data import Dataset

from pymongo import MongoClient
pymongo_client = MongoClient(os.environ.get('MONGODB_URI'))
pydb = pymongo_client.get_database()

import torch
import numpy as np
from tqdm import tqdm
# Define your custom dataset class
class FaceDataset(Dataset):
  def __init__(self, device = None):
    # Initialize your dataset
    self.dataset_labels = []
    self.dataset_inputs = []
    self.vectorizer = FaceVectorizer()
    self.num_classes = self.vectorizer.features_count
    self.one_hots = torch.eye(self.num_classes)
    self.device = torch.device('cpu')
    if device is not None:
      self.device = device

    model_dataset = dict()
    models = pydb.model.find({}, {'faces': 1, 'name': 1})
    model_count = pydb.model.count_documents({})
    for _ in tqdm(range(model_count), desc="Loading models"):
      model = next(models)
      model_name = model['name']
      face_count = len(model['faces'])
      if face_count >= 35: model_dataset[model_name] = face_count
      # model_dataset[model_name] = face_count

    names = dict()
    for model_name, _ in tqdm(model_dataset.items(), desc="Loading dataset"):
      face_filter = {'name': model_name}
      faces = pydb.face.find(face_filter, {'embedding_bin': 1, 'name': 1})
      face_count = pydb.face.count_documents(face_filter)
      for _ in range(face_count):
        face = next(faces)
        if face['name'] not in names:
          # print( self.vectorizer.get_label_from_name(face['name']))
          names[face['name']] = self.vectorizer.get_label_from_name(face['name']).argmax()
        sample_label = names[face['name']]
        sample_input = np.frombuffer(face['embedding_bin'], dtype=np.float32)
        self.dataset_inputs.append(sample_input)
        self.dataset_labels.append(sample_label)

      # if len(self.dataset_inputs) >= 1000000: break
    self.dataset_inputs = np.array(self.dataset_inputs)
    return

  def __len__(self):
    return len(self.dataset_inputs)

  def __getitem__(self, idx):
    data = torch.tensor(self.dataset_inputs[idx], dtype=torch.float32)
    label = self.dataset_labels[idx]
    label = self.one_hots[label]
    return data, label
