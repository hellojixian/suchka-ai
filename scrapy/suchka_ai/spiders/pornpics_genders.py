import scrapy
import re
import os
from ..items import ImageCaptionPairItem
from scrapy.loader import ItemLoader
import pickle
from dotenv import load_dotenv
load_dotenv()


class PornpicsSpider(scrapy.Spider):
    name = "pornpics_genders"

    genders = ['male','female','shemale']
    name_file = os.path.join(os.environ['PROJECT_FACEDB_PATH'], 'gender_names.pickle')
    allowed_domains = ["pornpics.com"]
    start_urls = ["https://www.pornpics.com/pornstars/male/",
                  "https://www.pornpics.com/pornstars/shemale",
                  "https://www.pornpics.com/pornstars/",]
    names = dict()

    def start_requests(self):
      if os.path.exists(self.name_file):
        with open(self.name_file, 'rb') as f:
          self.names = pickle.load(f)
      else:
        for gender in self.genders:
          self.names[gender] = set()

      res = super().start_requests()
      return res

    def parse(self, response):
      for name in response.css(".thumbwook a::attr(title)").getall():
        if name not in self.names:
          gender = response.url.split("/")[4].lower()
          if gender not in self.genders: gender = 'female'
          print(f"Detected {name} => {gender}")
          self.names[gender].add(name)
          self.save_names()

      for link in response.css(".paginator a::attr(href)").getall()[1:]:
          yield response.follow(link, callback=self.parse)

    def save_names(self):
      with open(self.name_file, 'wb') as f:
        pickle.dump(self.names, f)
