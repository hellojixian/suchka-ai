import os
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(project_root)

import pickle
from tqdm import tqdm
from sklearn.feature_extraction.text import CountVectorizer
from core.data_model import Gallery, Tag
from core.database import Database
db = Database()

pretrained_weights_path = f'{project_root}/pretrained/'

class TagAnalysis:
  def __init__(self):
    self.vectorizer = CountVectorizer(token_pattern=r'(?u)\b[^,]+\b')
    self.cached_file = f'{pretrained_weights_path}/tag.pkl'
    if os.path.exists(self.cached_file):
      self.load()
    else:
      corpus = self.load_training_data()
      self.train_vectorizer(corpus)
      self.save()

  def load_training_data(self):
    corpus = []
    tags = dict()
    tag_objs = Tag.objects().filter().only('id', 'name')
    tag_count = Tag.objects().count()
    for _ in tqdm(range(tag_count), desc="Loading training data"):
      tag = next(tag_objs)
      tags[tag.id] = tag.name

    galleries = Gallery.objects().only('tags')
    galleries_count = Gallery.objects().count()
    for _ in tqdm(range(galleries_count), desc="Loading training data"):
      gallery = next(galleries)
      tag_ids = [tag.id for tag in gallery.tags]
      gallery_tags = [tags[tag_id] for tag_id in tag_ids]
      corpus.append(','.join(gallery_tags))
    return corpus

  def train_vectorizer(self, corpus):
    self.data_matrix = self.vectorizer.fit_transform(corpus).toarray()

  def predict(self, tags):
    # corpus = ' '.join(tags)
    # X = self.vectorizer.transform([corpus])
    # predicted_labels = self.classifier.predict(X)
    # predicted_tags = self.vectorizer.inverse_transform(predicted_labels)
    # return predicted_tags
    return []

  def save(self):
    with open(self.cached_file, 'wb') as f:
      f.write(pickle.dumps([self.vectorizer, self.data_matrix]))

  def load(self):
    if not os.path.exists(self.cached_file): return
    with open(self.cached_file, 'rb') as f:
      [self.vectorizer, self.data_matrix] = pickle.load(f)

