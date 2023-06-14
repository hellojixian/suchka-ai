import os
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(project_root)

from core.data_model import Model
from core.face.batch_processor import process_batch
from dotenv import load_dotenv
load_dotenv()

storage_root = os.getenv("PROJECT_STORAGE_PATH")
facedb_root = os.getenv("PROJECT_FACEDB_PATH")
max_galleries = 15

def gather_images(model:Model):
  # sort galleries by gallery models count ascending
  model_images = []
  galleries = sorted(model.galleries, key=lambda g: g.is_solo)
  for i in range(len(galleries)):
    if i >= max_galleries: break
    gallery = model.galleries[i]
    gallery_path = os.path.join(storage_root, gallery.path)
    if not os.path.exists(gallery_path): continue
    images = [f'{gallery_path}/{f}' for f in os.listdir(gallery_path) if os.path.isfile(os.path.join(gallery_path, f)) and f.split('.')[-1].lower() == 'jpg']
    model_images += images
  return model_images

def process_model_faces(model:Model, pbar=None):
  model_images = gather_images(model)
  results = process_batch(images=model_images, device='gpu', threads=2, pbar=pbar, pbar_prefix=f'{model.name.rjust(20)}')

  pass