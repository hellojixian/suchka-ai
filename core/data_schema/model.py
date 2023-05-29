from mongoengine import *

class Face(EmbeddedDocument):
  path = StringField(required=True)
  source = StringField(required=True)
  embedding = StringField(required=True)

class Gallery(EmbeddedDocument):
  path = StringField(required=True)
  is_solo = BooleanField(required=True)

class Model(Document):
  name = StringField(required=True)
  gender = StringField()
  race = StringField()
  faces = ListField(EmbeddedDocumentField(Face))
  galleries = ListField(EmbeddedDocumentField(Gallery))
