from mongoengine import *
from dotenv import load_dotenv
load_dotenv()

# the fundamental gallery object
class Image(Document):
  gid = StringField(required=True)
  gallery = ReferenceField('Gallery')
  filename = StringField()
  url = StringField()
  meta = {
        'indexes': [
            {'fields': ['gallery']},
            {'fields': ['filename']},
            {'fields': ['gid']},
        ]
  }

  @property
  def path(self):
    return f"{self.gallery.path}/{self.filename}"