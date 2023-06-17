from mongoengine import *
from dotenv import load_dotenv
load_dotenv()

# tag object
class TagModel(EmbeddedDocument):
  model = LazyReferenceField('Model')
  gallery_count = IntField()

class TagChannel(EmbeddedDocument):
  channel = LazyReferenceField('Channel')
  gallery_count = IntField()

class TagRelatedTag(EmbeddedDocument):
  tag = LazyReferenceField('Tag')
  gallery_count = IntField()

class Tag(Document):
  name = StringField(required=True)
  related_tags = ListField(EmbeddedDocumentField('TagRelatedTag'))
  models = ListField(EmbeddedDocumentField('TagModel'))
  channels = ListField(EmbeddedDocumentField('TagChannel'))
  gallery_count = IntField()
  meta = {
      'indexes': [
          {'fields': ['name'], 'unique': True},
      ]
  }
