import os, sys
import traceback
import tqdm
import cv2
import concurrent.futures
import torch
from .detector import process_image, init_models

def load_images(images, pbar=None, pbar_prefix=""):
  images_dict = {}
  if pbar is not None:
    pbar.set_description(f'{pbar_prefix} : Loading'.ljust(35))
    pbar.reset(total=len(images))

  for image in images:
    images_dict[image] = cv2.imread(image)
    if pbar: pbar.update(1)
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

processor_models = None
def process_batch(images, device='cpu', threads=2, pbar=None, pbar_prefix=""):
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

  global processor_models
  if processor_models is None:
    processor_models = []
    if pbar: pbar.set_description(f'{pbar_prefix} : Initializing'.ljust(35))
    if pbar: pbar.reset(total=threads)
    for i in range(threads):
      device_id = f'cuda:{i % torch.cuda.device_count()}' if torch.cuda.is_available() and device == 'gpu' else 'cpu'
      processor_models.append(init_models(device=device_id))
      pbar.update(1)

  images = load_images(images=images, pbar=pbar, pbar_prefix=pbar_prefix)

  results = dict()
  with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
    futures = []
    if pbar: pbar.set_description(f'{pbar_prefix} : Processing'.ljust(35))
    if pbar: pbar.reset(total=len(images))

    for i, image in enumerate(images):
      models = processor_models[i % threads]
      future = executor.submit(process_image_worker, image, models=models, pbar=pbar if pbar is not None else None)
      futures.append(future)

    for future in concurrent.futures.as_completed(futures):
      result = future.result()
      if result[1] is not None: results[result[0]] = result[1]
  return results
