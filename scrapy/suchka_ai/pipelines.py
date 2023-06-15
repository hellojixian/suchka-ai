# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import hashlib
import json
import piexif
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from scrapy.pipelines.images import ImagesPipeline
from scrapy.utils.python import to_bytes
from scrapy.utils.misc import md5sum
from PIL import Image

import os, sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(project_root)

import core.data_model as model

def normalize_name(name):
  return " ".join([n.capitalize() for n in name.strip().split(' ')])

class SuchkaAiPipeline(ImagesPipeline):

  def item_completed(self, results, item, info):
    image_paths = [x["path"] for ok, x in results if ok]
    if not image_paths:
        raise DropItem("Item contains no images")
    # save item as data.json file with image path
    json_path = f"{self.store.basedir}/{item['source']}/{item['id']}/data.json"
    data = dict(item)

    # TODO:
    # should add gallery to database
    project_folder = self.store.basedir
    gallery_path = f"{self.store.basedir}/{item['source']}/{item['id']}"
    gallery_models = data['models'].split(', ') if data['models'] else []
    gallery_models = [normalize_name(m) for m in gallery_models]
    existing_models = model.Model.objects(name__in=gallery_models)
    existing_models = [m for m in existing_models]
    existing_model_names = [normalize_name(m.name) for m in existing_models]

    for model_name in gallery_models:
      if model_name not in existing_model_names:
        # create a new model
        new_model = model.Model(
          name = model_name,
          galleries = [],
          channels = [],
          tags = [],
        )
        new_model.save()
        existing_models.append(new_model)

    gallery_tags = data['tags'].split(', ') if data['tags'] else []
    existing_tags = model.Tag.objects(name__in=gallery_tags)
    existing_tags = [t for t in existing_tags]
    existing_tag_names = [m.name for m in existing_tags]
    for tag_name in gallery_tags:
      if tag_name not in existing_tag_names:
        new_tag = model.Tag(
          name = tag_name,
          models = [],
          galleries = [],
          channels = [],
        )
        new_tag.save()
        existing_tags.append(new_tag)

    gallery_channels = data['copyright'].split(', ') if data['copyright'] else []
    existing_channels = model.Channel.objects(name__in=gallery_channels)
    existing_channels = [c for c in existing_channels]
    existing_channel_names = [c.name for c in existing_channels]
    for channel_name in gallery_channels:
      if channel_name not in existing_channel_names:
        new_channel = model.Channel(
          name = channel_name,
          galleries = [],
          models = [],
          tags = []
        )
        new_channel.save()
        existing_channels.append(new_channel)

    gid = data['id']
    gallery = model.Gallery(
      gid = gid,
      url = data['url'],
      description = data['description'],
      source = data['source'],
      channels = existing_channels,
      tags = existing_tags,
      models = existing_models,
      path = gallery_path.replace(f"{project_folder}/", ""),
      is_solo = len(gallery_models) == 1,
    )
    gallery.save()
    # should add images to database
    for image_url in data['image_urls']:
      image_guid = hashlib.sha1(to_bytes(image_url)).hexdigest()
      local_path = f"{self.storage_root}/{gid}/{image_guid}.jpg"
      if not os.path.exists(local_path): continue
      image = Image(
        url = image_url,
        gid = gid,
        gallery = gallery,
        filename = f"{image_guid}.jpg",
      )
      image.save()
      gallery.images.append(image)
    gallery.save()

    del data['image_urls']
    with open(json_path, "w") as f:
      f.write(json.dumps(data))

    return item

  def image_downloaded(self, response, request, info, *, item=None):
    checksum = None
    for path, image, buf in self.get_images(response, request, info, item=item):
      if checksum is None:
          buf.seek(0)
          checksum = md5sum(buf)
      width, height = image.size
      self.store.persist_file(
          path,
          buf,
          info,
          meta={"width": width, "height": height},
          headers={"Content-Type": "image/jpeg"},
      )
      self.add_metadata(path, item)
    return checksum

  def add_metadata(self, image_path, item):
    full_path = f"{self.store.basedir}/{image_path}"
    image = Image.open(full_path)
    try:
      exif_dict = piexif.load(image.info['exif']) if 'exif' in image.info else {"0th": {}}
      if item['tags']:
        exif_dict["0th"][piexif.ImageIFD.XPKeywords] = item['tags'].encode(encoding='utf_16')

      if item['copyright']:
        exif_dict["0th"][piexif.ImageIFD.XPAuthor] = item['copyright'].encode(encoding='utf_16')
        exif_dict["0th"][piexif.ImageIFD.Copyright] = item['copyright'].encode(encoding='utf-8')

      if item['description']:
        exif_dict["0th"][piexif.ImageIFD.XPSubject] = item['description'].encode(encoding='utf_16')
        exif_dict["0th"][piexif.ImageIFD.ImageDescription] = item['description'].encode(encoding='utf-8')

      if item['source']:
        exif_dict["0th"][piexif.ImageIFD.XPComment] = item['source'].encode(encoding='utf_16')

      if item['models']:
        exif_dict["0th"][piexif.ImageIFD.Artist] = item['models'].encode(encoding='utf-8')

      if 'thumbnail' in exif_dict:
        exif_dict['thumbnail'] = None if exif_dict['thumbnail'] == b'' else exif_dict['thumbnail']

      exif_dict['Exif'][41728] = b''
      exif_bytes = piexif.dump(exif_dict)
      image.save(full_path, exif=exif_bytes)
      image.close()
    except Exception as e:
      image.close()
    finally:
      del image

  def file_path(self, request, response=None, info=None, *, item=None):
    image_guid = hashlib.sha1(to_bytes(request.url)).hexdigest()
    path = f"{item['source']}/{item['id']}/{image_guid}.jpg"
    return path
