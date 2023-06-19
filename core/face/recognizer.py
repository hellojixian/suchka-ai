import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)
weight_file = f'{os.path.dirname(project_root)}/pretrained/face_recognizer.pth'

import torch
import torch.nn as nn
from core.face.vectorizer import FaceVectorizer
import numpy as np

class FaceRecognizer(nn.Module):
  def __init__(self, device = None, bf16 = False):
    super(FaceRecognizer, self).__init__()

    self.vectorizer = FaceVectorizer()
    self.output_dim = self.vectorizer.features_count
    self.hidden_dim = 10000
    self.hidden_dim_2 = 5000

    self.classifier = nn.Sequential(
      nn.Linear(2622, self.hidden_dim),
      nn.ReLU(inplace=True),
      nn.Linear(self.hidden_dim, self.hidden_dim_2),
      nn.ReLU(inplace=True),
      nn.Linear(self.hidden_dim_2, self.output_dim),
    )
    self.softmax = nn.Softmax(dim=1)
    self.load_weights()
    self.device = torch.device('cpu')
    if device is not None:
      self.device = device
      self.to(device)
    if bf16: self.half()
    self.bf16 = bf16

  def forward(self, x):
    out = self.classifier(x)
    return out

  def evalaute(self):
    import numpy as np
    from tqdm import tqdm
    from pymongo import MongoClient
    pymongo_client = MongoClient(os.environ.get('MONGODB_URI'))
    pydb = pymongo_client.get_database()

    dataset_labels = []
    dataset_inputs = []
    batch_size = 1000
    model_dataset = dict()
    models = pydb.model.find({}, {'faces': 1, 'name': 1})
    model_count = pydb.model.count_documents({})
    for _ in tqdm(range(model_count), desc="Loading models"):
      model = next(models)
      model_name = model['name']
      face_count = len(model['faces'])
      if face_count >= 100:
        model_dataset[model_name] = face_count

    names = dict()
    for model_name, _ in tqdm(model_dataset.items(), desc="Loading dataset"):
      face_filter = {'name': model_name}
      faces = pydb.face.find(face_filter, {'embedding_bin': 1, 'name': 1})
      face_count = pydb.face.count_documents(face_filter)
      for _ in range(face_count):
        face = next(faces)
        if face['name'] not in names:
          # print( self.vectorizer.get_label_from_name(face['name']))
          names[face['name']] = self.vectorizer.get_label_from_name(face['name']).argmax()
        sample_label = names[face['name']]
        sample_input = np.frombuffer(face['embedding_bin'], dtype=np.float32)
        dataset_inputs.append(sample_input)
        dataset_labels.append(sample_label)
      # if len(dataset_inputs) > batch_size * 2:break
    self.eval()

    num_classes = self.vectorizer.features_count
    one_hots = torch.eye(num_classes)
    correct_count = 0
    random_ids = np.random.randint(0, len(dataset_inputs), size=(batch_size,))
    for random_id in random_ids:
      inputs = torch.tensor(np.array([dataset_inputs[random_id]])).to(self.device)
      if self.bf16: inputs = inputs.half()
      label = one_hots[dataset_labels[random_id]].numpy()
      label_real = self.vectorizer.get_name_from_label(label)
      label_pred, probs = self.predict(inputs)
      if label_pred == label_real: correct_count+=1
    print(f'Accuracy: {(correct_count/batch_size):.4f}')
    return

  def predict_batch(self, embeddings):
    with torch.no_grad():
      x = self.forward(embeddings)
      x = self.softmax(x)
      for i in range(x.shape[0]):
        pos = x[i].argmax().cpu().detach().numpy()
        label = torch.Tensor(np.zeros(self.output_dim))
        label[pos] = 1
        x[i] = label
      return x

  def predict(self, embedding):
    with torch.no_grad():
      x = self.forward(embedding)
      x = self.softmax(x)
      pos = x.argmax().cpu().detach().numpy()
      probs = x[0, pos]
      label = np.zeros(self.output_dim)
      label[pos] = 1
      return [self.vectorizer.get_name_from_label(label), probs]

  def save_weights(self):
    torch.save(self.state_dict(), weight_file)
    return

  def load_weights(self, path = None):
    if path is None: path = weight_file
    if not os.path.exists(path): return
    state_dict = torch.load(path)
    self.load_state_dict(state_dict)
    self.eval()
    return

