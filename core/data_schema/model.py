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

# tag object
class TagModel(EmbeddedDocument):
  model = ReferenceField(Model, reverse_delete_rule=DO_NOTHING)
  galleries = IntField(required=True)

class Tag(Document):
  name = StringField(required=True)
  models = ListField(EmbeddedDocumentField('TagModel'))
  channels = ListField(ReferenceField('Channel', reverse_delete_rule=DO_NOTHING))
  galleries = ListField(ReferenceField('Gallery', reverse_delete_rule=DO_NOTHING))

# channel object
class ChannelModel(EmbeddedDocument):
  model = ReferenceField(Model, reverse_delete_rule=DO_NOTHING)
  galleries = IntField(required=True)

class ChanneTag(EmbeddedDocument):
  tag = ReferenceField(Tag, reverse_delete_rule=DO_NOTHING)
  galleries = IntField(required=True)

class Channel(Document):
  name = StringField(required=True)
  galleries = ListField(ReferenceField('Gallery', reverse_delete_rule=DO_NOTHING))
  models = ListField(ReferenceField('ChannelModel', reverse_delete_rule=DO_NOTHING))
  tags = ListField(ReferenceField('ChannelTag', reverse_delete_rule=DO_NOTHING))

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
