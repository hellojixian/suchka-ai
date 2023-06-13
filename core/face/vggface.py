import torch
import torch.nn as nn

import os
project_root = os.path.abspath(os.path.join(os.path.dirname('../')))
weight_file = f'{project_root}/pretrained/vggface.pth'

class VGGFace(nn.Module):
  def __init__(self):
    super(VGGFace, self).__init__()

    self.features = nn.Sequential(
      nn.Conv2d(3, 64, kernel_size=3, padding=1),
      nn.ReLU(inplace=True),
      nn.Conv2d(64, 64, kernel_size=3, padding=1),
      nn.ReLU(inplace=True),
      nn.MaxPool2d(kernel_size=2, stride=2),

      nn.Conv2d(64, 128, kernel_size=3, padding=1),
      nn.ReLU(inplace=True),
      nn.Conv2d(128, 128, kernel_size=3, padding=1),
      nn.ReLU(inplace=True),
      nn.MaxPool2d(kernel_size=2, stride=2),

      nn.Conv2d(128, 256, kernel_size=3, padding=1),
      nn.ReLU(inplace=True),
      nn.Conv2d(256, 256, kernel_size=3, padding=1),
      nn.ReLU(inplace=True),
      nn.Conv2d(256, 256, kernel_size=3, padding=1),
      nn.ReLU(inplace=True),
      nn.MaxPool2d(kernel_size=2, stride=2),

      nn.Conv2d(256, 512, kernel_size=3, padding=1),
      nn.ReLU(inplace=True),
      nn.Conv2d(512, 512, kernel_size=3, padding=1),
      nn.ReLU(inplace=True),
      nn.Conv2d(512, 512, kernel_size=3, padding=1),
      nn.ReLU(inplace=True),
      nn.MaxPool2d(kernel_size=2, stride=2),

      nn.Conv2d(512, 512, kernel_size=3, padding=1),
      nn.ReLU(inplace=True),
      nn.Conv2d(512, 512, kernel_size=3, padding=1),
      nn.ReLU(inplace=True),
      nn.Conv2d(512, 512, kernel_size=3, padding=1),
      nn.ReLU(inplace=True),
      nn.MaxPool2d(kernel_size=2, stride=2),
    )

    self.classifier = nn.Sequential(
      nn.Conv2d(512, 4096, kernel_size=7),
      nn.ReLU(inplace=True),
      nn.Dropout(0.5),
      nn.Conv2d(4096, 4096, kernel_size=1),
      nn.ReLU(inplace=True),
      nn.Dropout(0.5),
      nn.Conv2d(4096, 2622, kernel_size=1),
    )

    self.flatten = nn.Flatten()
    self.softmax = nn.Softmax(dim=1)
    self.load_weights()

  def forward(self, x):
    x = self.features(x)
    x = self.classifier(x)
    x = self.flatten(x)
    return x

  def embedding(self, x):
    x = self.features(x)
    x = self.classifier(x)
    x = self.flatten(x)
    return x

  def load_weights(self, path = None):
    if path is None: path = weight_file
    if not os.path.exists(path): raise Exception(f'No such file: {path}')
    state_dict = torch.load(path)
    self.load_state_dict(state_dict)
    self.eval()