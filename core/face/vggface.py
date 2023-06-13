import torch.nn as nn

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

          nn.Conv2d(512, 4096, kernel_size=7),
          nn.ReLU(inplace=True),
          nn.Dropout(0.5),
          nn.Conv2d(4096, 4096, kernel_size=1),
          nn.ReLU(inplace=True),
          nn.Dropout(0.5),
          nn.Conv2d(4096, 2622, kernel_size=1),
          nn.Flatten()
      )

    #   self.flatten = nn.Flatten()
    #   self.softmax = nn.Softmax(dim=1)

  def forward(self, x):
      x = self.features(x)
    #   x = self.flatten(x)
    #   x = self.softmax(x)
      return x
