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


import sys

class SuchkaAiPipeline(ImagesPipeline):

  def item_completed(self, results, item, info):
    image_paths = [x["path"] for ok, x in results if ok]
    if not image_paths:
        raise DropItem("Item contains no images")
    # save item as data.json file with image path
    json_path = f"{self.store.basedir}/{item['source']}/{item['id']}/data.json"
    data = dict(item)
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
    exif_dict = piexif.load(image.info['exif']) if 'exif' in image.info else {"0th": {}}
    exif_dict["0th"][piexif.ImageIFD.XPKeywords] = item['tags'].encode(encoding='utf_16')
    exif_dict["0th"][piexif.ImageIFD.XPAuthor] = item['copyright'].encode(encoding='utf_16')
    exif_dict["0th"][piexif.ImageIFD.XPSubject] = item['description'].encode(encoding='utf_16')
    exif_dict["0th"][piexif.ImageIFD.XPComment] = item['source'].encode(encoding='utf_16')
    exif_dict["0th"][piexif.ImageIFD.ImageDescription] = item['description'].encode(encoding='utf-8')
    exif_dict["0th"][piexif.ImageIFD.Artist] = item['copyright'].encode(encoding='utf-8')
    exif_dict["0th"][piexif.ImageIFD.Copyright] = item['copyright'].encode(encoding='utf-8')
    exif_bytes = piexif.dump(exif_dict)
    image.save(full_path, exif=exif_bytes)

  def file_path(self, request, response=None, info=None, *, item=None):
    image_guid = hashlib.sha1(to_bytes(request.url)).hexdigest()
    path = f"{item['source']}/{item['id']}/{image_guid}.jpg"
    return path
