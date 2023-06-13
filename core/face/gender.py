import torch
import torch.nn as nn

import os
project_root = os.path.abspath(os.path.join(os.path.dirname('../')))
weight_file = f'{project_root}/pretrained/gender.pth'
labels = ["female", "male"]

class Gender(nn.Module):
  def __init__(self):
    super(Gender, self).__init__()
    in_channels = 512
    self.classifier = nn.Sequential(
      nn.Conv2d(in_channels, 4096, kernel_size=7),
      nn.ReLU(inplace=True),
      nn.Dropout(0.5),
      nn.Conv2d(4096, 4096, kernel_size=1),
      nn.ReLU(inplace=True),
      nn.Dropout(0.5),
      nn.Conv2d(4096, len(labels), kernel_size=1),
    )
    self.flatten = nn.Flatten(start_dim=0)
    self.softmax = nn.Softmax(dim=0)
    self.load_weights()

  def forward(self, x):
    x = self.classifier(x)
    x = self.flatten(x)
    x = self.softmax(x)
    return x

  def predict(self, x):
    x = self.forward(x)
    x = x.argmax()
    return labels[x]

  def load_weights(self, path = None):
    if path is None: path = weight_file
    if not os.path.exists(path): raise Exception(f'No such file: {path}')
    state_dict = torch.load(path)
    self.load_state_dict(state_dict)
    self.eval()