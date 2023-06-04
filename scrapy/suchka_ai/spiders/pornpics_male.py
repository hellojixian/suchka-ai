import scrapy
import re
import os
from ..items import ImageCaptionPairItem
from scrapy.loader import ItemLoader
import pickle
from dotenv import load_dotenv
load_dotenv()


class PornpicsSpider(scrapy.Spider):
    name = "pornpics_male"

    name_file = os.path.join(os.environ['PROJECT_FACEDB_PATH'],"male_names.pickle")
    allowed_domains = ["pornpics.com"]
    start_urls = ["https://www.pornpics.com/pornstars/male/"]
    names = set()

    def start_requests(self):
      if os.path.exists(self.name_file):
        with open(self.name_file, 'rb') as f:
          self.names = pickle.load(f)

      res = super().start_requests()
      return res

    def parse(self, response):
      for name in response.css(".thumbwook a::attr(title)").getall():
        if name not in self.names:
          self.names.add(name)
          self.save_names()

      for link in response.css(".paginator a::attr(href)").getall()[1:]:
          yield response.follow(link, callback=self.parse)

    def save_names(self):
      with open(self.name_file, 'wb') as f:
        pickle.dump(self.names, f)
