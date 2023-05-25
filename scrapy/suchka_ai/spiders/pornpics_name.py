import scrapy
import re
import os
import json
from ..items import ImageCaptionPairItem
from scrapy.loader import ItemLoader

class PornpicsSpider(scrapy.Spider):
    name = "pornpics_name"
    realname = "pornpics"
    allowed_domains = ["pornpics.com"]
    start_urls = ["https://www.pornpics.com/channels/list/0-9/"]

    def start_requests(self):
        url_template = 'https://www.pornpics.com/galleries/{gid}/'
        root_path = os.path.join(self.settings.get('IMAGES_STORE'), self.realname)
        gids = [f for f in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, f))]
        for gid in gids:
          data_file = os.path.join(self.settings.get('IMAGES_STORE'), self.realname, gid, 'data.json')
          with open(data_file, "r") as f:
            data = json.load(f)
          if data.get('models') and data.get('url'): continue
          url = url_template.format(gid=gid)
          yield scrapy.Request(url, dont_filter=True)

    def parse(self, response):
        models = ", ".join(response.css(".gallery-info .gallery-info__item:nth-child(2) a span::text").getall())
        gid = re.search(r"var ID\s+=\s+'([0-9]+)'",response.text).group(1)

        data_file = os.path.join(self.settings.get('IMAGES_STORE'), self.realname, gid, 'data.json')
        if os.path.exists(data_file):
            with open(data_file, "r") as f:
                data = json.load(f)
            data['models'] = models
            data['url'] = response.url
            with open(data_file, "w") as f:
                json.dump(data, f)
            print("Updated: ", data_file)


