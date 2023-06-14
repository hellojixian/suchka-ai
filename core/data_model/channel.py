from mongoengine import *
from dotenv import load_dotenv
load_dotenv()

# channel object
class ChannelModel(EmbeddedDocument):
  model = ReferenceField('Model')
  galleries = ListField(ReferenceField('Gallery'))
  count = IntField()

class ChannelTag(EmbeddedDocument):
  tag = ReferenceField('Tag')
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
          {'fields': ['name'], 'unique': True},
          {'fields': ['parent']},
          {'fields': ['children']},
          {'fields': ['galleries']},
      ]
  }
