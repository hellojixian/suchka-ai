from .channel import *
from .face import *
from .gallery import *
from .model import *
from .tag import *
from .image import *

def build_indexes():
  Tag.ensure_indexes()
  Gallery.ensure_indexes()
  Model.ensure_indexes()
  Face.ensure_indexes()
  Channel.ensure_indexes()
  Image.ensure_indexes()
  return