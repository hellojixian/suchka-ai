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
        process_model_faces(model=model, pbar=pbar)
        sender.put(['FINISHED', model_id])
      except Exception as e:
        print(f"Error {e}")
        traceback.print_exc()


if __name__ == '__main__':
  # Register the signal handler for SIGINT
  signal.signal(signal.SIGINT, signal_handler)

  # Create face process in a dedicated process
  manager = mp.Manager()
  globals()['manager'] = manager

  workers = {}
  # Create a worker process
  for i in range(num_processes):
    sender = manager.Queue()
    reciver = manager.Queue()
    pbar = tqdm.tqdm(desc=f'Worker {i}').reset()
    worker = mp.Process(target=model_processor, args=(sender,reciver,pbar,))
    worker.start()
    workers[worker.pid] = (worker, sender, reciver, pbar,)
    pbar.set_description(f'Worker {i} (PID: {worker.pid})')

  results = []
  # using pymongo for faster query
  model_collection = pydb.model.find({}).sort('galleries.size', 1)
  def next_model(collection, pbar):
    """Get next model with face not extracted"""
    model = next(collection)
    while ('faces_extracted' in model.keys() and model['faces_extracted'] == True) \
      or (' ' not in model['name'].strip()):
      model = next(collection)
      pbar.update(1)
    return model

  with tqdm.tqdm(range(pydb.model.count_documents({})), desc=f'Process model faces') as pbar:
    for pid, (worker, reciver, sender, _) in workers.items():
      sender.put(['MODEL_ID', next_model(model_collection, pbar=pbar)['_id']])

    while True:
      for pid, (worker, reciver, sender, _) in workers.items():
        if reciver.empty(): continue
        queue_item = reciver.get()
        if queue_item[0] == 'FINISHED':
          pbar.update(1)
          sender.put(['MODEL_ID', next_model(model_collection, pbar=pbar)['_id']])



