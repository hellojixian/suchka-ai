from mongoengine import *
from dotenv import load_dotenv
load_dotenv()

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
