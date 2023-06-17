from enum import Enum
from mongoengine import *
from dotenv import load_dotenv
load_dotenv()

class ModelTag(EmbeddedDocument):
  tag = LazyReferenceField('Tag')
  galleries = ListField(LazyReferenceField('Gallery'))
  count = IntField()

class ModelChannel(EmbeddedDocument):
  channel = LazyReferenceField('Channel')
  galleries = ListField(LazyReferenceField('Gallery'))
  count = IntField()

class ModelRelatedModel(EmbeddedDocument):
  model = LazyReferenceField('Model')
  galleries = ListField(LazyReferenceField('Gallery'))
  count = IntField()

class GenderEnum(Enum):
    MALE = 'male'
    FEMALE = 'female'
    SHEMALE = 'shemale'

class Model(Document):
  name = StringField(required=True)
  gender = EnumField(GenderEnum)
  race = StringField()
  faces = ListField(LazyReferenceField('Face'))
  face_extracted = BooleanField()
  facial_gender = EnumField(GenderEnum)
  galleries = ListField(LazyReferenceField('Gallery'))
  tags = ListField(EmbeddedDocumentField('ModelTag'))
  channels = ListField(EmbeddedDocumentField('ModelChannel'))
  related_models = ListField(EmbeddedDocumentField('ModelRelatedModel'))
  meta = {
      'indexes': [
          {'fields': ['name'], 'unique': True},
          {'fields': ['gender']},
          {'fields': ['facial_gender']},
          {'fields': ['galleries']},
      ]
  }
