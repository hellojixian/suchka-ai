#!/usr/bin/env python3
import os
import sys
import cv2

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

import tqdm
import numpy as np

from dotenv import load_dotenv
load_dotenv()

project_storage_root = os.getenv("PROJECT_STORAGE_PATH")
channel_logo_dir = f"{project_storage_root}/channels"

logo_files = []
logo_files += [os.path.join(root, file) for root, dirs, files in os.walk(channel_logo_dir+'/jpg') for file in files if file.endswith((".jpg", ".png"))]
logo_files += [os.path.join(root, file) for root, dirs, files in os.walk(channel_logo_dir+'/png') for file in files if file.endswith((".jpg", ".png"))]
# logo_files = ['/storage/suchka-storage/channels/jpg/aziani-iron.jpg']
change_threshold = 10
for logo_file in tqdm.tqdm(logo_files, desc="Processing channel logos"):
  image = cv2.imread(logo_file, cv2.IMREAD_UNCHANGED)
  gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

  try:
    left_spacing = 0
    for x in range(image.shape[1]):
      left_spacing += 1
      diff_count = np.count_nonzero(np.abs((gray_image[:, 0] - gray_image[:, x])))
      if diff_count > change_threshold :break

    right_spacing = 0
    for x in range(image.shape[1] - 1, -1, -1):
      right_spacing += 1
      diff_count = np.count_nonzero(np.abs((gray_image[:, 0] - gray_image[:, x])))
      if diff_count > change_threshold :break

    if right_spacing <= left_spacing: continue

    height, width, _ = image.shape
    new_width = width - (right_spacing - left_spacing)

    cropped_image = image[:, 0:new_width]
    # print(new_width, width, right_spacing, left_spacing)
    # print(cropped_image.shape, logo_file)
    # if path extension is png, save as png
    # if logo_file.endswith('.png'):
      # cropped_image = cv2.imdecode(cropped_image, cv2.IMREAD_UNCHANGED)
    cv2.imwrite(logo_file, cropped_image)
  except Exception as e:
    print(e)
    print(logo_file)
    continue

