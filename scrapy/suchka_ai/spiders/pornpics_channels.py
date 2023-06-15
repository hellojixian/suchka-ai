import scrapy
import json
import re
import os
from ..items import ImageCaptionPairItem
from scrapy.loader import ItemLoader
import tqdm
from scrapy.http import Request

from dotenv import load_dotenv
load_dotenv()

from core.data_model.channel import Channel
import base64
import cv2

class PornpicsSpider(scrapy.Spider):
    """for fetching channel logo and URL"""
    name = "pornpics_channels"
    allowed_domains = ["pornpics.com"]
    folder_name = 'pornpics'

    def start_requests(self):
      channels = Channel.objects()
      total_channels = Channel.objects().count()
      for _ in tqdm.tqdm(range(total_channels), desc="Scanning channels"):
        channel = next(channels)
        channel_url_name = channel.name.lower().replace(' ', '-')
        channel_url = f"https://www.pornpics.com/channels/{channel_url_name}/"
        yield Request(channel_url, dont_filter=True)

    def download_image(self, response, filename):
      folder = os.path.join(self.settings.get('IMAGES_STORE'), self.folder_name)
      if not os.path.exists(folder): os.mkdir(folder)
      with open(f"{folder}/{filename}", 'wb') as f:
        f.write(response.body)

    def generate_jpg_logo(self, png_logo, background):
      pass

    def parse(self, response):
      channels = ", ".join(response.css(".gallery-info__item a::text").getall())
      gid = re.search(r"var ID\s+=\s+'([0-9]+)'",response.text).group(1)
      data_folder = os.path.join(self.settings.get('IMAGES_STORE'), self.folder_name)
      data_file = f"{data_folder}/{gid}/data.json"
      if not os.path.exists(data_file): return
      with open(data_file, 'r') as json_file:
        data = json.load(json_file)
      if data['copyright'] != channels:
        self.log(f"Updating {gid} from [{data['copyright']}] to [{channels}]")
        data['copyright'] = channels
        with open(data_file, 'w') as json_file:
          json_file.write(json.dumps(data))