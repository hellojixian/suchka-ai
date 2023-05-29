#!/usr/bin/env python3
import json
import os
import piexif
from PIL import Image
root_path = os.path.dirname(os.getcwd())+"/output/pornpics/"
# list all folders in the output folder
folders = [f for f in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, f))]
for gid in folders:
  g_folder = os.path.join(root_path, gid)
  data_file = os.path.join(g_folder, 'data.json')
  if not os.path.exists(data_file): continue
  with open(data_file, "r") as f:
    data = json.load(f)
  # list all jpg files in the g_folder
  jpgs = [f for f in os.listdir(g_folder) if os.path.isfile(os.path.join(g_folder, f)) and f.endswith('.jpg')]
  for image in jpgs:
    full_path = os.path.join(g_folder, image)
    image = Image.open(full_path)
    try:
      exif_dict = piexif.load(image.info['exif']) if 'exif' in image.info else {"0th": {}}
      exif_dict["0th"][piexif.ImageIFD.XPKeywords] = data['tags'].encode(encoding='utf_16')
      exif_dict["0th"][piexif.ImageIFD.XPAuthor] = data['copyright'].encode(encoding='utf_16')
      exif_dict["0th"][piexif.ImageIFD.XPSubject] = data['description'].encode(encoding='utf_16')
      exif_dict["0th"][piexif.ImageIFD.XPComment] = data['source'].encode(encoding='utf_16')
      exif_dict["0th"][piexif.ImageIFD.ImageDescription] = data['description'].encode(encoding='utf-8')
      exif_dict["0th"][piexif.ImageIFD.Artist] = data['models'].encode(encoding='utf-8')
      exif_dict["0th"][piexif.ImageIFD.Copyright] = data['copyright'].encode(encoding='utf-8')
      exif_dict['thumbnail'] = None if exif_dict['thumbnail'] == b'' else exif_dict['thumbnail']
      exif_bytes = piexif.dump(exif_dict)
    finally:
      image.save(full_path, exif=exif_bytes)
      image.close()
      del image
  print(f"Updated {gid}")
