from mongoengine import *
from dotenv import load_dotenv
load_dotenv()

# the fundamental gallery object
class Gallery(Document):
  gid = StringField(required=True)
  url = StringField()
  description = StringField()
  source = StringField()
  channels = ListField(ReferenceField('Channel'))
  tags = ListField(ReferenceField('Tag'))
  models = ListField(ReferenceField('Model'))
  images = ListField(ReferenceField('Image'))
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
