from mongoengine import *
from dotenv import load_dotenv
load_dotenv()

# channel object
class ChannelModel(EmbeddedDocument):
  model = LazyReferenceField('Model')
  galleries = ListField(LazyReferenceField('Gallery'))
  count = IntField()

class ChannelTag(EmbeddedDocument):
  tag = LazyReferenceField('Tag')
  galleries = ListField(LazyReferenceField('Gallery'))
  count = IntField()

class ChannelLogo(EmbeddedDocument):
  background_color = StringField()
  url = StringField()
  png = StringField()
  jpg = StringField()

class Channel(Document):
  name = StringField(required=True)
  url = StringField()
  logo = EmbeddedDocumentField('ChannelLogo')
  parent = LazyReferenceField('Channel')
  galleries = ListField(LazyReferenceField('Gallery'))
  children = ListField(LazyReferenceField('Channel'))
  models = ListField(EmbeddedDocumentField('ChannelModel'))
  tags = ListField(EmbeddedDocumentField('ChannelTag'))
  meta = {
      'indexes': [
          {'fields': ['name'], 'unique': True},
          {'fields': ['parent']},
          {'fields': ['children']},
          {'fields': ['galleries']},
      ]
  }
