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


class PornpicsSpider(scrapy.Spider):
    name = "pornpics_channels"
    allowed_domains = ["pornpics.com"]
    folder_name = 'pornpics'

    def start_requests(self):
      data_folder = os.path.join(self.settings.get('IMAGES_STORE'), self.folder_name)

      galleries = set()
      folders = [f for f in os.listdir(data_folder) if os.path.isdir(os.path.join(data_folder, f))]
      for f in folders: galleries.add(f)

      # sort galleries by name
      galleries = sorted(galleries, key=lambda f: f.name)
      for f in tqdm.tqdm(galleries, desc="Scanning data folder"):
        data_file = f"{f.path}/data.json"
        if not os.path.exists(data_file): continue
        with open(data_file, 'r') as json_file:
          data = json.load(json_file)
        if data['copyright'] is None: continue
        if ',' in data['copyright']: continue
        url = data['url']
        yield Request(url, dont_filter=True)
      # res = super().start_requests()


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