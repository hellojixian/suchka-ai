import scrapy
import json
import re
import os, sys
import traceback

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
sys.path.append(project_root)

import tqdm
from scrapy.http import Request
from scrapy.spidermiddlewares.httperror import HttpError

from dotenv import load_dotenv
load_dotenv()

from core.data_model.channel import Channel, ChannelLogo
from core.database import Database
db = Database()

from PIL import Image
from urllib.parse import urlparse, urlunparse
import cv2
import numpy as np

logo_width = 260

class PornpicsSpider(scrapy.Spider):
    """for fetching channel logo and URL"""
    name = "pornpics_channels"
    folder_name = 'channels'

    def start_requests(self):
      self.channel_folder = f"{self.settings.get('IMAGES_STORE')}/channels"
      if not os.path.exists(self.channel_folder): os.mkdir(self.channel_folder)
      if not os.path.exists(f"{self.channel_folder}/png"): os.mkdir(f"{self.channel_folder}/png")
      if not os.path.exists(f"{self.channel_folder}/jpg"): os.mkdir(f"{self.channel_folder}/jpg")

      channels = Channel.objects()
      total_channels = Channel.objects().count()
      for _ in tqdm.tqdm(range(total_channels), desc="Scanning channels"):
        channel = next(channels)
        channel._id = channel.id
        # if channel.logo:
        #   self.log(f"Skipping existing channel: {channel.name}")
        #   continue
        channel.logo = ChannelLogo()
        channel_url_name = channel.name.lower().replace(' ', '+')
        channel_url = f"https://www.pornpics.com/channels/{channel_url_name}/"
        yield Request(channel_url, dont_filter=True, errback=self.errback_httpbin, meta={'channel': channel})

    def errback_httpbin(self, failure):
      # Check if the failure is an HttpError with a 404 status code
      if failure.check(HttpError) and failure.value.response.status == 404:
        # Handle the 404 error here
        channel = failure.request.meta['channel']
        channel_url_name = channel.name.lower().replace(' ', '+')
        channel_url = f"https://www.pornpics.com/?q={channel_url_name}/"
        self.log(f"404 Error: Retry another url {channel_url}")
        yield Request(channel_url, dont_filter=True, meta={'channel': channel})


    def download_image(self, response):
      channel = response.meta['channel']
      filename = channel.name.lower().replace(' ', '-') + '.png'
      filepath = f"{self.channel_folder}/png/{filename}"

      image_bytes = response.body
      nparr = np.frombuffer(image_bytes, np.uint8)
      image = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
      cv2.imwrite(filepath, image)

      # apply background color and save as jpg
      jpg_filename = channel.name.lower().replace(' ', '-') + '.jpg'
      jpg_filepath = f"{self.channel_folder}/jpg/{jpg_filename}"

      hex_color = channel.logo.background_color.lstrip('#')
      r = int(hex_color[0:2], 16)
      g = int(hex_color[2:4], 16)
      b = int(hex_color[4:6], 16)
      background_color = (r, g, b)

      png_image = Image.open(filepath)
      background = Image.new("RGB", png_image.size, background_color)
      background.paste(png_image, (0, 0), png_image)
      background.save(jpg_filepath, 'JPEG', quality=120)

      channel.logo.png = filename
      channel.logo.jpg = jpg_filename
      if channel.url: channel.save()
      return

    def parse_channel(self, response):
      channel = response.meta['channel']

      parsed_url = urlparse(response.url)
      scheme = parsed_url.scheme
      netloc = parsed_url.netloc
      path = parsed_url.path
      params = ''
      query = ''
      fragment = ''

      cleaned_url = urlunparse((scheme, netloc, path, params, query, fragment))
      channel.url = cleaned_url
      if channel.logo.png: channel.save()
      return

    def parse(self, response):
      channel = response.meta['channel']
      logo_style = response.css(".sponsor-type-4 a.left-side::attr(style)").get()
      channel_url = response.css(".sponsor-type-4 a.left-side::attr(href)").get()
      matches = re.search(r"url\(\s*(.+)\)\s+(.*)\;", logo_style)

      if not matches: return
      channel.logo.url = matches.group(1)
      channel.logo.background_color = matches.group(2) #e.g.: #000000

      if not channel.url:
        yield response.follow(channel_url, callback=self.parse_channel, meta={'channel': channel})
      if not channel.logo.png:
        yield response.follow(channel.logo.url, callback=self.download_image, meta={'channel': channel})
