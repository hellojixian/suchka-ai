from mongoengine import *
from dotenv import load_dotenv
load_dotenv()

# the fundamental gallery object
class Gallery(Document):
  gid = StringField(required=True)
  url = StringField()
  description = StringField()
  source = StringField()
  channels = ListField(LazyReferenceField('Channel'))
  tags = ListField(LazyReferenceField('Tag'))
  models = ListField(LazyReferenceField('Model'))
  images = ListField(LazyReferenceField('Image'))
  path = StringField(required=True)
  is_solo = BooleanField(required=True)
  meta = {
        'indexes': [
            {'fields': ['gid'], 'unique': True},
            {'fields': ['url'], 'unique': True},
            {'fields': ['models']},
            {'fields': ['channels']},
            {'fields': ['tags']},
        ]
    }
