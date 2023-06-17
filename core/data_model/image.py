from mongoengine import *
from dotenv import load_dotenv
load_dotenv()

# the fundamental gallery object
class Image(Document):
  gid = StringField(required=True)
  gallery = LazyReferenceField('Gallery')
  filename = StringField()
  url = StringField()
  meta = {
        'indexes': [
            {'fields': ['url'], 'unique': True},
            {'fields': ['filename'], 'unique': True},
            {'fields': ['gallery']},
            {'fields': ['gid']},
        ]
  }

  @property
  def path(self):
    return f"{self.gallery.path}/{self.filename}"