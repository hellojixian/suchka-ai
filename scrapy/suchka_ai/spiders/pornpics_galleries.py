import scrapy
import os, sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
sys.path.append(project_root)

import tqdm
from scrapy.http import Request

from dotenv import load_dotenv
load_dotenv()

from core.data_model import Image, Gallery
from core.database import Database
db = Database()

from scrapy.utils.python import to_bytes
import hashlib
from mongoengine import NotUniqueError

class PornpicsSpider(scrapy.Spider):
    """for fetching channel logo and URL"""
    name = "pornpics_galleries"
    folder_name = 'pornpics'

    def start_requests(self):
      self.storage_root = f"{self.settings.get('IMAGES_STORE')}/{self.folder_name}"

      galleries = Gallery.objects().order_by('gid')
      galleries_channels = Gallery.objects().count()
      for _ in tqdm.tqdm(range(galleries_channels), desc="Scanning galleries"):
        gallery = next(galleries)
        if gallery.images and len(gallery.images) > 0:
          self.log(f"Skipping existing gallery: {gallery.url}")
          continue
        yield Request(gallery.url, dont_filter=True, meta={'gallery': gallery})

    def parse(self, response):
      image_urls = response.css(".gallery-ps4 .thumbwook a::attr(href)").getall()
      gallery = response.meta['gallery']
      gid = gallery.gid
      for image_url in image_urls:
        image_guid = hashlib.sha1(to_bytes(image_url)).hexdigest()
        local_path = f"{self.storage_root}/{gid}/{image_guid}.jpg"
        if not os.path.exists(local_path): continue
        try:
          image = Image(
            url = image_url,
            gid = gid,
            gallery = gallery,
            filename = f"{image_guid}.jpg",
          )
          image.save()
          gallery.images.append(image)
        except NotUniqueError as e:
          self.log(f"Skip: Image URL exists: {image_url}")
        except Exception as e:
          self.log(f"Error: {e}")
      gallery.save()

