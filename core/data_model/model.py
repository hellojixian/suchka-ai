from enum import Enum
from mongoengine import *
from dotenv import load_dotenv
load_dotenv()

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

class GenderEnum(Enum):
    MALE = 'male'
    FEMALE = 'female'
    SHEMALE = 'shemale'

class Model(Document):
  name = StringField(required=True)
  gender = EnumField(GenderEnum)
  facial_gender = EnumField(GenderEnum)
  race = StringField()
  faces = ListField(ReferenceField('Face'))
  galleries = ListField(ReferenceField('Gallery'))
  tags = ListField(EmbeddedDocumentField('ModelTag'))
  channels = ListField(EmbeddedDocumentField('ModelChannel'))
  models = ListField(EmbeddedDocumentField('ModelModel'))
  meta = {
      'indexes': [
          {'fields': ['name']},
          {'fields': ['gender']},
          {'fields': ['facial_gender']},
          {'fields': ['galleries']},
      ]
  }
