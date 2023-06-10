from mongoengine import *

# model object
class ModelFace(EmbeddedDocument):
  path = StringField(required=True)
  source = StringField(required=True)

class ModelTag(EmbeddedDocument):
  tag = ReferenceField('Tag', reverse_delete_rule=DO_NOTHING)
  count = IntField(required=True)

class Model(Document):
  name = StringField(required=True)
  gender = StringField()
  race = StringField()
  faces = ListField(EmbeddedDocumentField(ModelFace))
  galleries = ListField(ReferenceField('Gallery', reverse_delete_rule=DO_NOTHING))
  tags = ListField(ReferenceField('ModelTag', reverse_delete_rule=DO_NOTHING))
  channels = ListField(ReferenceField('Channel', reverse_delete_rule=DO_NOTHING))
  meta = {
      'indexes': [
          {'fields': ['name']},
          {'fields': ['galleries']},
          {'fields': ['channels']},
          {'fields': ['tags']},
      ]
  }
# tag object
class TagModel(EmbeddedDocument):
  model = ReferenceField(Model, reverse_delete_rule=DO_NOTHING)
  galleries = IntField(required=True)

class Tag(Document):
  name = StringField(required=True)
  models = ListField(EmbeddedDocumentField('TagModel'))
  channels = ListField(ReferenceField('Channel', reverse_delete_rule=DO_NOTHING))
  galleries = ListField(ReferenceField('Gallery', reverse_delete_rule=DO_NOTHING))
  meta = {
      'indexes': [
          {'fields': ['name']},
          {'fields': ['models']},
          {'fields': ['channels']},
          {'fields': ['galleries']},
      ]
  }

# channel object
class ChannelModel(EmbeddedDocument):
  model = ReferenceField(Model, reverse_delete_rule=DO_NOTHING)
  galleries = IntField(required=True)

class ChanneTag(EmbeddedDocument):
  tag = ReferenceField(Tag, reverse_delete_rule=DO_NOTHING)
  galleries = IntField(required=True)

class Channel(Document):
  name = StringField(required=True)
  logo = StringField()
  background_color = StringField()
  url = StringField()
  parent = ReferenceField('Channel', reverse_delete_rule=DO_NOTHING)
  children = ListField(ReferenceField('Channel', reverse_delete_rule=DO_NOTHING))
  galleries = ListField(ReferenceField('Gallery', reverse_delete_rule=DO_NOTHING))
  models = ListField(ReferenceField('ChannelModel', reverse_delete_rule=DO_NOTHING))
  tags = ListField(ReferenceField('ChannelTag', reverse_delete_rule=DO_NOTHING))
  meta = {
      'indexes': [
          {'fields': ['name']},
          {'fields': ['parent']},
          {'fields': ['models']},
          {'fields': ['children']},
          {'fields': ['galleries']},
          {'fields': ['tags']},
      ]
  }

# the fundamental gallery object
class Gallery(Document):
  gid = StringField(required=True)
  url = StringField()
  description = StringField()
  source = StringField()
  channels = ListField(ReferenceField(Channel))
  tags = ListField(ReferenceField(Tag))
  models = ListField(ReferenceField(Model))
  path = StringField(required=True)
  is_solo = BooleanField(required=True)
  meta = {
        'indexes': [
            {'fields': ['gid']},
            {'fields': ['models']},
            {'fields': ['channels']},
            {'fields': ['tags']},
        ]
    }
