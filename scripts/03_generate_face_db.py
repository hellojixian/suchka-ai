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

from core.data_model import Model, Face, Gallery
from core.database import Database
db = Database()

import multiprocessing as mp

from pymongo import MongoClient
pymongo_client = MongoClient(os.environ.get('MONGODB_URI'))
pydb = pymongo_client.get_database()

project_folder = os.getenv("PROJECT_STORAGE_PATH")
faces_dir = os.getenv("PROJECT_FACEDB_PATH")


def signal_handler(signal, frame):
  print("Ctrl+C pressed. Exiting gracefully...")
  manager = globals()['manager']
  manager.shutdown()
  sys.exit()

def face_prcoessor(queue):
  """ face processor should be a standalone process,
  coomunicate with other child process via unix socket """
  try:
    print("face_prcoessor queue:", queue)
    while True:
      if not queue.empty():
        data = queue.get()
        print(f"face_prcoessor: {data}  {os.getpid()}")
      # time.sleep(1)
  except Exception as e:
    print(f"Error {e}")
    traceback.print_exc()
  return

def process_model(model_id, queue):
  try:
    print("process_model process ID:", os.getpid())
    queue.put(f'get face for model {model_id}')

    model = Model.objects(id=model_id).first()
    print(f"Checking {model['name']} ")
  except Exception as e:
    print(f"Error {e}")
    traceback.print_exc()
  return

if __name__ == '__main__':
  num_processes = 2
  # Register the signal handler for SIGINT
  signal.signal(signal.SIGINT, signal_handler)

  # Create face process in a dedicated process
  manager = mp.Manager()
  queue = manager.Queue()

  globals()['manager'] = manager
  face_process = mp.Process(target=face_prcoessor, args=(queue,))
  face_process.start()

  # Create a multiprocessing Pool
  pool = manager.Pool(processes=num_processes)

  results = []
  # using pymongo for faster query
  model_collection = pydb.model.find({}).sort('galleries.size', 1)
  for _ in tqdm.tqdm(range(pydb.model.count_documents({})), desc=f'Check face folders'):
    model_mongo = next(model_collection)
    if 'face_extracted' in model_mongo.keys() and model_mongo['face_extracted']: continue
    model_id = model_mongo['_id']
    print(f"main process id: {os.getpid()}")
    result = pool.apply_async(process_model, (model_id, queue,))
    results.append(result)

  # Wait for all tasks to complete and collect the results
  final_results = [result.get() for result in results]
  # Close the Pool to release resources
  pool.close()
  pool.join()
