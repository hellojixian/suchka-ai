#!/usr/bin/env python3
import os
import sys
import traceback
import time

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

import tqdm
import signal

from dotenv import load_dotenv
load_dotenv()

from core.data_model import Model
from core.processor.model_face import process_model_faces
from core.database import Database
db = Database()

import multiprocessing as mp

from pymongo import MongoClient
pymongo_client = MongoClient(os.environ.get('MONGODB_URI'))
pydb = pymongo_client.get_database()

num_processes = 6
task_timeout = 90

def signal_handler(signal, frame):
  print("Ctrl+C pressed. Exiting gracefully...")
  manager = globals()['manager']
  manager.shutdown()
  sys.exit()

def model_processor(sender, receiver, pbar):
  while True:
    if receiver.empty(): continue
    queue_item = receiver.get()
    if queue_item[0] == 'MODEL_ID':
      model_id = queue_item[1]
      try:
        model = Model.objects(id=model_id).first()
        should_process = True
        if model.face_extracted == True: should_process = False
        if ' ' not in model.name.strip(): should_process = False
        if should_process: process_model_faces(model=model, pbar=pbar)
        sender.put(['FINISHED', model_id])
      except Exception as e:
        print(f"Error {e}")
        traceback.print_exc()

if __name__ == '__main__':
  if not os.environ['CUDA_LAUNCH_BLOCKING'] or not os.environ['TORCH_USE_CUDA_DSA']:
    # enable these setting to prevent this error:
    # RuntimeError: CUDA error: misaligned address
    # CUDA kernel errors might be asynchronously reported at some other API call, so the stacktrace below might be incorrect.
    # For debugging consider passing CUDA_LAUNCH_BLOCKING=1.
    # Compile with `TORCH_USE_CUDA_DSA` to enable device-side assertions.
    # raise Exception("CUDA_LAUNCH_BLOCKING and TORCH_USE_CUDA_DSA must be set to 1")
    pass
  # Register the signal handler for SIGINT
  signal.signal(signal.SIGINT, signal_handler)

  # Create face process in a dedicated process
  manager = mp.Manager()
  globals()['manager'] = manager

  def start_worker(pbar=None, sender=None, reciver=None):
    if not sender: sender = manager.Queue()
    if not reciver: reciver = manager.Queue()
    if not pbar: pbar = tqdm.tqdm(desc=f'Worker started', total=0)
    worker = mp.Process(target=model_processor, args=(sender,reciver,pbar,))
    worker.start()
    worker.last_update = time.time()
    pbar.set_description(f'Worker started (PID: {worker.pid})')
    return worker.pid, (worker, sender, reciver, pbar)

  workers = {}
  # Create a worker process
  for i in range(num_processes):
    pid, data = start_worker()
    workers[pid] = data

  results = []
  # using pymongo for faster query
  model_collection = pydb.model.find({}).sort('galleries.size', 1)
  def next_model(collection, pbar):
    """Get next model with face not extracted"""
    model = next(collection)
    while ('face_extracted' in model.keys() and model['face_extracted'] == True) \
      or (' ' not in model['name'].strip()):
      model = next(collection)
      pbar.update(1)
    return model

  with tqdm.tqdm(range(pydb.model.count_documents({})), desc=f'Process model faces') as pbar:
    for pid, (worker, reciver, sender, _) in workers.items():
      sender.put(['MODEL_ID', next_model(model_collection, pbar=pbar)['_id']])
      worker.last_update = time.time()

    while True:
      for pid, (worker, reciver, sender, pbar) in workers.items():
        if time.time() - worker.last_update > task_timeout:
          print(f'Worker {pid} timeout, restarting...')
          worker.terminate()
          new_pid, data = start_worker(pbar=pbar, sender=reciver, reciver=sender)
          workers[new_pid] = data
          data[2].put(['MODEL_ID', next_model(model_collection, pbar=pbar)['_id']])
          data[0].last_update = time.time()
          del workers[pid]
          break

        if reciver.empty(): continue
        queue_item = reciver.get()
        if queue_item[0] == 'FINISHED':
          pbar.update(1)
          sender.put(['MODEL_ID', next_model(model_collection, pbar=pbar)['_id']])
          worker.last_update = time.time()



