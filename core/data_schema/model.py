from mongoengine import *

# model object
class ModelFace(EmbeddedDocument):
  path = StringField(required=True)
  source = StringField(required=True)

class ModelTag(EmbeddedDocument):
  tag = ReferenceField('Tag', reverse_delete_rule=DO_NOTHING)
  galleries = ListField(ReferenceField('Gallery', reverse_delete_rule=DO_NOTHING))
  count = IntField()

class ModelChannel(EmbeddedDocument):
  channel = ReferenceField('Channel', reverse_delete_rule=DO_NOTHING)
  galleries = ListField(ReferenceField('Gallery', reverse_delete_rule=DO_NOTHING))
  count = IntField()

class ModelModel(EmbeddedDocument):
  model = ReferenceField('Model', reverse_delete_rule=DO_NOTHING)
  galleries = ListField(ReferenceField('Gallery', reverse_delete_rule=DO_NOTHING))
  count = IntField()

class Model(Document):
  name = StringField(required=True)
  gender = StringField()
  race = StringField()
  faces = ListField(EmbeddedDocumentField(ModelFace))
  galleries = ListField(ReferenceField('Gallery', reverse_delete_rule=DO_NOTHING))
  tags = ListField(ReferenceField('ModelTag', reverse_delete_rule=DO_NOTHING))
  channels = ListField(ReferenceField('ModelChannel', reverse_delete_rule=DO_NOTHING))
  models = ListField(ReferenceField('ModelModel', reverse_delete_rule=DO_NOTHING))
  meta = {
      'indexes': [
          {'fields': ['name']},
          {'fields': ['galleries']},
      ]
  }
# tag object
class TagModel(EmbeddedDocument):
  model = ReferenceField('Model', reverse_delete_rule=DO_NOTHING)
  galleries = ListField(ReferenceField('Gallery', reverse_delete_rule=DO_NOTHING))
  count = IntField()

class TagChannel(EmbeddedDocument):
  channel = ReferenceField('Channel', reverse_delete_rule=DO_NOTHING)
  galleries = ListField(ReferenceField('Gallery', reverse_delete_rule=DO_NOTHING))
  count = IntField()

class Tag(Document):
  name = StringField(required=True)
  models = ListField(EmbeddedDocumentField('TagModel'))
  channels = ListField(ReferenceField('TagChannel', reverse_delete_rule=DO_NOTHING))
  galleries = ListField(ReferenceField('Gallery', reverse_delete_rule=DO_NOTHING))
  meta = {
      'indexes': [
          {'fields': ['name']},
          {'fields': ['galleries']},
      ]
  }

# channel object
class ChannelModel(EmbeddedDocument):
  model = ReferenceField(Model, reverse_delete_rule=DO_NOTHING)
  galleries = ListField(ReferenceField('Gallery', reverse_delete_rule=DO_NOTHING))
  count = IntField()

class ChanneTag(EmbeddedDocument):
  tag = ReferenceField(Tag, reverse_delete_rule=DO_NOTHING)
  galleries = ListField(ReferenceField('Gallery', reverse_delete_rule=DO_NOTHING))
  count = IntField()

class Channel(Document):
  name = StringField(required=True)
  logo = StringField()
  background_color = StringField()
  url = StringField()
  galleries = ListField(ReferenceField('Gallery', reverse_delete_rule=DO_NOTHING))
  parent = ReferenceField('Channel', reverse_delete_rule=DO_NOTHING)
  children = ListField(ReferenceField('Channel', reverse_delete_rule=DO_NOTHING))
  models = ListField(ReferenceField('ChannelModel', reverse_delete_rule=DO_NOTHING))
  tags = ListField(ReferenceField('ChannelTag', reverse_delete_rule=DO_NOTHING))
  meta = {
      'indexes': [
          {'fields': ['name']},
          {'fields': ['parent']},
          {'fields': ['children']},
          {'fields': ['galleries']},
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
