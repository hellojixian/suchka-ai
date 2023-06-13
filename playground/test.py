import os, sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from core.data_model import Model
from core.database import Database
from core.face.batch_processor import process_batch

db = Database()

image_root = os.environ['PROJECT_STORAGE_PATH']

model = Model.objects(name='Red Xxx').first()
model_images = []
for i in range(len(model.galleries)):
  if i >= 30: break
  gallery = model.galleries[i]
  gallery_path = os.path.join(image_root, gallery.path)
  # find all jpg files in the gallery_path
  images = [f'{gallery_path}/{f}' for f in os.listdir(gallery_path) if os.path.isfile(os.path.join(gallery_path, f)) and f.split('.')[-1].lower() == 'jpg']
  model_images += images
results = process_batch(images=model_images, device='gpu', threads=2, silent=False)
# results = process_batch(images=model_images, device='cpu', threads=4, silent=False)

for image_path, faces in results.items():
  print(image_path)
  for face in faces:
    print(face['gender'])
  print('-------------------')