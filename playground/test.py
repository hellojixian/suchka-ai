import os, sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from core.data_model import Model
from core.database import Database
from core.face.batch_processor import process_batch
import tqdm

db = Database()

image_root = os.environ['PROJECT_STORAGE_PATH']

model = Model.objects(name='Red Xxx').first()
model_images = []
for i in range(len(model.galleries)):
  if i >= 3: break
  gallery = model.galleries[i]
  gallery_path = os.path.join(image_root, gallery.path)
  # find all jpg files in the gallery_path
  images = [f'{gallery_path}/{f}' for f in os.listdir(gallery_path) if os.path.isfile(os.path.join(gallery_path, f)) and f.split('.')[-1].lower() == 'jpg']
  model_images += images
pbar = tqdm.tqdm().reset()
results = process_batch(images=model_images, device='gpu', pbar=pbar, pbar_prefix=f'{model.name.rjust(20)}')
# results = process_batch(images=model_images, device='cpu', threads=4, pbar=pbar, pbar_prefix=f'{model.name.rjust(20)}')

face_count = 0
for image_path, faces in results.items():
  print(image_path)
  for face in faces:
    print(face['gender'])
    face_count += 1
  print('-------------------')
print(f'face count: {face_count}')