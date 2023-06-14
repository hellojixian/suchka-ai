import os, sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from core.data_model import Model
from core.database import Database
from core.processor.model_face import process_model_faces
import tqdm

db = Database()

image_root = os.environ['PROJECT_STORAGE_PATH']
# test_model_name = 'Red Xxx'
test_model_name = 'Jack Hammer'
test_model_name = 'Jack Vegas'
test_model_name = 'Hannah Vivienne'
# fb39e3df182d0b7629d6ebb96431c29c45086c9d
model = Model.objects(name=test_model_name).first()
process_model_faces(model=model, pbar=tqdm.tqdm(desc=f'Worker 0', total=0))