#!/usr/bin/env python3
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from core.database import Database
db = Database()

from core.face.recognizer import FaceRecognizer
from core.face.dataset import FaceDataset
import torch
from torch import nn
from torch.nn import CrossEntropyLoss, DataParallel
from torch.optim.lr_scheduler import StepLR

from torch.utils.data import DataLoader, random_split
from tqdm import tqdm

device = torch.device("cuda:1")
dataset = FaceDataset(device=device)

split_ratio = 0.95

# Define the batch size for your DataLoader
batch_size = 2048
num_epochs = 500
val_batch_size = 100

# Create a DataLoader instance
train_size = int(split_ratio * len(dataset))
val_size = len(dataset) - train_size
train_dataset, val_dataset = random_split(dataset, [train_size, val_size])
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=val_batch_size)

# dataloader = DataLoader(dataset, batch_size=batch_size)

# Create an instance of the DNN classifier model
model = FaceRecognizer(device=device)

total_params = sum(p.numel() for p in model.parameters())
print(f'Total params: {total_params/1024/1024}')

# Define your loss function
criterion = CrossEntropyLoss()

# Define your optimizer
# optimizer = torch.optim.AdamW(model.parameters(), lr=0.0005)
optimizer = torch.optim.AdamW(model.parameters(), lr=0.05)
scheduler = StepLR(optimizer, step_size=10, gamma=0.1)

model.train()

# Training loop
with torch.enable_grad():
  for epoch in range(num_epochs):
    with tqdm(train_loader, unit="batch") as t:
      loss_list = []
      for data in t:
        inputs, labels = data

        inputs = inputs.to(model.device)
        labels = labels.to(model.device)

        # Forward pass
        outputs = model(inputs)

        # Compute the loss
        loss = criterion(outputs, labels)

        # Backward pass and optimization
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        loss_list.append(loss.item())
        loss_mean = torch.mean(torch.tensor(loss_list))
        t.set_description(f"Epoch [{epoch+1}/{num_epochs}], Loss: {loss_mean:.4f} LR: {scheduler.get_last_lr()[0]:.4f}")

    scheduler.step()
    # print current leanring rate
    model.save_weights()

    with tqdm(val_loader, unit="batch") as x:
      accuracy_list = []
      for val_data in x:
        val_intputs, val_labels = val_data
        val_intputs = val_intputs.to(model.device)
        val_labels = val_labels.to(model.device)
        val_outputs = model.predict_batch(val_intputs)
        # compare outputs and labels to calculate accuracy
        accuracy = (val_outputs.argmax(dim=1) == val_labels.argmax(dim=1)).float().mean()
        accuracy_list.append(accuracy)
        accuracy_mean = torch.mean(torch.tensor(accuracy_list))
        x.set_description(f"Epoch [{epoch+1}/{num_epochs}], Accuracy: {accuracy_mean:.4f}")

