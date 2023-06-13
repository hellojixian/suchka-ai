import os, sys
import traceback
import tqdm
import cv2
import concurrent.futures
import torch
from .detector import process_image, init_models

def load_images(images, silent=False):
  images_dict = {}
  for image in tqdm.tqdm(images, desc=f'Load model images', disable=silent):
    images_dict[image] = cv2.imread(image)
  return images_dict

def process_image_worker(img, models, pbar=None):
  res = None
  try:
    res = process_image(img, models)
  except Exception as e:
    print(e)
    traceback.print_exc()
  if pbar: pbar.update(1)
  return (img, res)

def process_batch(images, device='cpu', threads=2, silent=False):
  """
  this module is used to process the batch of images
  using multi threads

  # Returns:

  for image_path, faces in results.items():
  print(image_path)
  for face in faces:
    print(face['gender'])
  print('-------------------')

  """
  # load images into memory
  images = load_images(images=images, silent=silent)
  processor_models = []

  for i in range(threads):
    device_id = f'cuda:{i % torch.cuda.device_count()}' if torch.cuda.is_available() and device == 'gpu' else 'cpu'
    processor_models.append(init_models(device=device_id))

  results = dict()
  with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
    futures = []
    with tqdm.tqdm(total=len(images), disable=silent) as pbar:
      for i, image in enumerate(images):
        models = processor_models[i % threads]
        future = executor.submit(process_image_worker, image, models=models, pbar=pbar if not silent else None)
        futures.append(future)

      for future in concurrent.futures.as_completed(futures):
        result = future.result()
        if result[1] is not None: results[result[0]] = result[1]
  return results

# def test(device='cpu'):
#   init_models(device=device)