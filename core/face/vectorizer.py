import os
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(project_root)

import pickle
from tqdm import tqdm
from sklearn.feature_extraction.text import CountVectorizer
from core.data_model import Model

import numpy as np
pretrained_weights_path = f'{project_root}/pretrained/'

class FaceVectorizer():
  def __init__(self):
    self.vectorizer = CountVectorizer(token_pattern=r'(?u)\b[^,]+\b')
    self.cached_file = f'{pretrained_weights_path}/face_vectoriner.pkl'
    if os.path.exists(self.cached_file):
      self.load()
    else:
      names = self.load_training_data()
      self.train_vectorizer(names)
      self.save()

  @property
  def features_count(self):
    return len(self.vectorizer.vocabulary_)

  def load_training_data(self):
    models = Model.objects().all().only('id', 'name', 'faces')
    model_count = models.count()
    names = set()
    for _ in tqdm(range(model_count), desc="Loading model names"):
      model = next(models)
      if len(model.faces) >= 100: names.add(model.name)
    return names

  def get_label_from_name(self, name):
    return self.vectorizer.transform([name]).toarray()[0]

  def get_name_from_label(self, label):
    label = label.reshape(1, -1)
    label_res = self.vectorizer.inverse_transform(label)
    name = ' '.join(label_res[0])
    name = ' '.join(w.capitalize() for w in name.split())
    return name

  def train_vectorizer(self, corpus):
    self.vectorizer.fit_transform(corpus).toarray()

  def save(self):
    with open(self.cached_file, 'wb') as f:
      f.write(pickle.dumps(self.vectorizer))

  def load(self):
    if not os.path.exists(self.cached_file): return
    with open(self.cached_file, 'rb') as f:
      self.vectorizer = pickle.load(f)