import os, sys
import traceback
# os.environ["CUDA_VISIBLE_DEVICES"] = ""

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)
import tqdm
# from core.face.detector import load_image, process_image
from core.data_model import Model
from core.database import Database

import cv2
db = Database()

image_root = os.environ['PROJECT_STORAGE_PATH']
import torch
# from mtcnn import MTCNN
# face_detector = MTCNN(scale_factor=0.5, min_face_size=50)

from facenet_pytorch import MTCNN
face_detectors =[
  MTCNN(factor=0.5, min_face_size=60, device='cuda:0'),
  MTCNN(factor=0.5, min_face_size=60, device='cuda:1'),
  # MTCNN(factor=0.5, min_face_size=60, device='cpu'),
  # MTCNN(factor=0.5, min_face_size=60, device='cpu'),
  # MTCNN(factor=0.5, min_face_size=60, device='cpu'),
  # MTCNN(factor=0.5, min_face_size=60, device='cpu'),
]

model = Model.objects(name='Red Xxx').first()
model_images = []
for i in range(len(model.galleries)):
  if i >= 30: break
  gallery = model.galleries[i]
  gallery_path = os.path.join(image_root, gallery.path)
  # find all jpg files in the gallery_path
  images = [f'{gallery_path}/{f}' for f in os.listdir(gallery_path) if os.path.isfile(os.path.join(gallery_path, f)) and f.split('.')[-1].lower() == 'jpg']
  model_images += images

model_image_dict = {}
for model_image in tqdm.tqdm(model_images, desc=f'Load model images'):
  model_image_dict[model_image] = cv2.imread(model_image)

image_dataset = []
for _ in range(100): image_dataset += model_image_dict.values()

import concurrent.futures
num_workers = len(face_detectors)

# @tf.function
def my_process_image(img, id, pbar):
  # process_image(img, gpu_id=gpu_id)
  try:
    with torch.no_grad():
      res = face_detectors[id].detect(img, landmarks=True)
  except Exception as e:
    print(e)
    traceback.print_exc()
  pbar.update(1)
  return

current_processor_id = 0
# Create a ThreadPoolExecutor with a maximum of 10 workers (threads)
with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
    # Create a list to hold the futures
    futures = []

    # Iterate over the model images and submit tasks to the executor
    with tqdm.tqdm(total=len(image_dataset)) as pbar:
      for img in image_dataset:
          # Assign the current GPU ID to the task
          future = executor.submit(my_process_image, img, id=current_processor_id, pbar=pbar)
          # Update the current GPU ID for the next task (round-robin)
          current_processor_id = (current_processor_id + 1) % len(face_detectors)
          futures.append(future)

      for future in concurrent.futures.as_completed(futures):
        pass
# K.clear_session()
# gc.collect()