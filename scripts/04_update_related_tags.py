#!/usr/bin/env python3
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from tqdm import tqdm
from core.data_model import Gallery, Tag
from core.database import Database
db = Database()

from pymongo import MongoClient
pymongo_client = MongoClient(os.environ.get('MONGODB_URI'))
pydb = pymongo_client.get_database()

tags = dict()
tag_objs = Tag.objects().filter().only('id')
tag_count = Tag.objects().count()
for _ in tqdm(range(tag_count), desc="Loading tags"):
  tag = next(tag_objs)
  tags[tag.id] = []

galleries = dict()
galleries_objs = Gallery.objects().only('tags')
galleries_count = Gallery.objects().count()
galleries_objs.batch_size(100)
for _ in tqdm(range(galleries_count), desc="Loading galleries"):
  gallery = next(galleries_objs)
  tag_ids = [tag.id for tag in gallery.tags]
  galleries[gallery.id] = tag_ids
  for tag_id in tag_ids:
    tags[tag_id].append(gallery.id)

tag_collection = pydb.tag.find({}).batch_size(10)
for _ in tqdm(range(tag_count), desc="process tags"):
  tag = next(tag_collection)
  tag_id = tag['_id']
  tag_galleries = tags[tag_id]
  related_tags = dict()
  for gallery_id in tag_galleries:
    gallery_tags = galleries[gallery_id]
    for related_tag_id in gallery_tags:
      if related_tag_id == tag_id: continue
      if related_tag_id not in related_tags:
        related_tags[related_tag_id] = 0
      related_tags[related_tag_id] += 1

  related_tags_arr = []
  for related_tag_id in related_tags:
    related_tags_arr.append({
      'tag': related_tag_id,
      'gallery_count': related_tags[related_tag_id]
    })
  pydb.tag.update_one({'_id': tag_id}, {'$set': {'related_tags': related_tags_arr}})
