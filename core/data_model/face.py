import os
import numpy as np
from mongoengine import *
from dotenv import load_dotenv
load_dotenv()

# model object
class Face(Document):
  name = StringField(required=True)
  filename = StringField(required=True)
  source = StringField(required=True)
  embedding_bin = BinaryField()
  model = ReferenceField('Model')
  gallery = ReferenceField('Gallery')
  meta = {
      'indexes': [
          {'fields': ['name']},
          {'fields': ['model']},
          {'fields': ['gallery']},
      ]
  }
  @property
  def path(self):
    return  f"{os.getenv('PROJECT_FACEDB_PATH')}/{self.name}/{self.filename}"

  @property
  def embedding(self):
    return np.frombuffer(self.embedding_bin, dtype=np.float32)
