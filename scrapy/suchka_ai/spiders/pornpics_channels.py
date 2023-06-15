import scrapy
import json
import re
import os, sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
sys.path.append(project_root)

import tqdm
from scrapy.http import Request

from dotenv import load_dotenv
load_dotenv()

from core.data_model.channel import Channel, ChannelLogo
from core.database import Database
db = Database()

import base64
import cv2
import numpy as np

logo_width = 260

os.environ['ROBOTSTXT_OBEY'] = 'False'

class PornpicsSpider(scrapy.Spider):
    """for fetching channel logo and URL"""
    name = "pornpics_channels"
    folder_name = 'channels'

    def start_requests(self):
      self.channel_folder = self.settings.get('IMAGES_STORE')
      if not os.path.exists(self.channel_folder): os.mkdir(self.channel_folder)
      channels = Channel.objects()
      total_channels = Channel.objects().count()
      for _ in tqdm.tqdm(range(total_channels), desc="Scanning channels"):
        channel = next(channels)
        channel.logo = ChannelLogo()
        channel_url_name = channel.name.lower().replace(' ', '-')
        channel_url = f"https://www.pornpics.com/channels/{channel_url_name}/"
        yield Request(channel_url, dont_filter=True, meta={'channel': channel})

    def download_image(self, response):
      channel = response.meta['channel']
      filename = channel.name.lower().replace(' ', '-') + '.png'
      filepath = f"{self.channel_folder}/{filename}"

      image_bytes = response.body
      nparr = np.frombuffer(image_bytes, np.uint8)
      image = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

      # crop the image to logo_width
      height, width, _ = image.shape
      new_width = 380
      crop_x = (width - new_width) // 2
      crop_y = 0
      cropped_image = image[crop_y:crop_y + height, crop_x:crop_x + new_width]
      cv2.imwrite(filepath, cropped_image)

      # apply background color and save as jpg
      jpg_filename = channel.name.lower().replace(' ', '-') + '.jpg'
      jpg_filepath = f"{self.channel_folder}/{jpg_filename}"

      hex_color = channel.logo.background_color.lstrip('#')
      r = int(hex_color[0:2], 16)
      g = int(hex_color[2:4], 16)
      b = int(hex_color[4:6], 16)
      background_color = (r, g, b)
      background = np.full((height, width, 3), background_color, dtype=np.uint8)
      jpg_image = cv2.bitwise_or(cropped_image, background)
      cv2.imwrite(jpg_filepath, jpg_image, [cv2.IMWRITE_JPEG_QUALITY, 90])

      channel.logo.png = filename
      if channel.url is not None: channel.save()
      return

    def parse_channel(self, response):
      channel = response.meta['channel']
      channel.url = response.url
      if channel.logo.jpg is not None: channel.save()
      return

    def parse(self, response):
      channel = response.meta['channel']
      logo_style = response.css(".sponsor-type-4 a.left-side::attr(style)").get()
      channel_url = response.css(".sponsor-type-4 a.left-side::attr(href)").get()
      matches = re.search(r"url\(\s*(.+)\)\s+(.*)\;", logo_style)

      if not matches: return
      channel.logo.url = matches.group(1)
      channel.logo.background_color = matches.group(2) #e.g.: #000000

      yield response.follow(channel_url, callback=self.parse_channel, meta={'channel': channel})
      yield response.follow(channel.logo.url, callback=self.download_image, meta={'channel': channel})
