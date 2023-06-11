import os
from mongoengine import *
from dotenv import load_dotenv
load_dotenv()

# model object
class Face(Document):
  name = StringField(required=True)
  filename = StringField(required=True)
  source = StringField(required=True)
  embedding = ListField(FloatField())
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

class ModelTag(EmbeddedDocument):
  tag = ReferenceField('Tag')
  galleries = ListField(ReferenceField('Gallery'))
  count = IntField()

class ModelChannel(EmbeddedDocument):
  channel = ReferenceField('Channel')
  galleries = ListField(ReferenceField('Gallery'))
  count = IntField()

class ModelModel(EmbeddedDocument):
  model = ReferenceField('Model')
  galleries = ListField(ReferenceField('Gallery'))
  count = IntField()

class Model(Document):
  name = StringField(required=True)
  gender = StringField()
  race = StringField()
  faces = ListField(ReferenceField('Face'))
  galleries = ListField(ReferenceField('Gallery'))
  tags = ListField(EmbeddedDocumentField('ModelTag'))
  channels = ListField(EmbeddedDocumentField('ModelChannel'))
  models = ListField(EmbeddedDocumentField('ModelModel'))
  meta = {
      'indexes': [
          {'fields': ['name']},
          {'fields': ['galleries']},
      ]
  }
# tag object
class TagModel(EmbeddedDocument):
  model = ReferenceField('Model')
  gallery_count = IntField()

class TagChannel(EmbeddedDocument):
  channel = ReferenceField('Channel')
  gallery_count = IntField()

class Tag(Document):
  name = StringField(required=True)
  models = ListField(EmbeddedDocumentField('TagModel'))
  channels = ListField(EmbeddedDocumentField('TagChannel'))
  gallery_count = IntField()
  meta = {
      'indexes': [
          {'fields': ['name']},
      ]
  }

# channel object
class ChannelModel(EmbeddedDocument):
  model = ReferenceField(Model)
  galleries = ListField(ReferenceField('Gallery'))
  count = IntField()

class ChannelTag(EmbeddedDocument):
  tag = ReferenceField(Tag)
  galleries = ListField(ReferenceField('Gallery'))
  count = IntField()

class Channel(Document):
  name = StringField(required=True)
  logo = StringField()
  background_color = StringField()
  url = StringField()
  galleries = ListField(ReferenceField('Gallery'))
  parent = ReferenceField('Channel')
  children = ListField(ReferenceField('Channel'))
  models = ListField(EmbeddedDocumentField('ChannelModel'))
  tags = ListField(EmbeddedDocumentField('ChannelTag'))
  meta = {
      'indexes': [
          {'fields': ['name']},
          {'fields': ['parent']},
          {'fields': ['children']},
          {'fields': ['galleries']},
      ]
  }

# the fundamental gallery object
class Gallery(Document):
  gid = StringField(required=True)
  url = StringField()
  description = StringField()
  source = StringField()
  channels = ListField(ReferenceField(Channel))
  tags = ListField(ReferenceField(Tag))
  models = ListField(ReferenceField(Model))
  path = StringField(required=True)
  is_solo = BooleanField(required=True)
  meta = {
        'indexes': [
            {'fields': ['gid']},
            {'fields': ['models']},
            {'fields': ['channels']},
            {'fields': ['tags']},
        ]
    }
