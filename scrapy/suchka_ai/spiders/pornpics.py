import scrapy

# https://www.pornpics.com/channels/list/0-9/
# https://www.pornpics.com/channels/list/a/

from ..items import ImageCaptionPairItem
from scrapy.loader import ItemLoader
import re

class PornpicsSpider(scrapy.Spider):
    name = "pornpics"
    allowed_domains = ["pornpics.com"]
    start_urls = ["https://www.pornpics.com/channels/list/0-9/"]

    def parse(self, response):
        if response.url in self.start_urls:
            yield from self.parse_channel_list(response)
        # response.l
        pair = ItemLoader(item=ImageCaptionPairItem(), response=response)
        pair.load_item()

    def parse_channel_list(self, response):
        search_url = "https://www.pornpics.com/search/srch.php?q={keyword}&lang=en&limit={limit}&offset={offset}"
        search_page_limit = 100
        for channel in response.css("#content .models-list .list-item a"):
            channel_url = channel.css("::attr(href)").get()
            match = re.search(r"^/channels/([^/]*)/$", channel_url)
            if not match: continue
            keyword = match.group(1)
            keyword = keyword.replace("-", "+")
            count = (int)(re.search(r"(\d+)", channel.css("span::text").get()).group(1))
            for offset in range(0, count, search_page_limit):
                data_url = search_url.format(keyword=keyword, limit=search_page_limit, offset=offset)
                yield scrapy.Request(data_url, callback=self.parse_data_list)

        for link in response.css("#content .alphabet .alpha a::attr(href)").getall():
            yield scrapy.Request(link, callback=self.parse_channel_list)

    def parse_data_list(self, response):
        for data in response.json():
            data_url = data['g_url']
            yield scrapy.Request(data_url, callback=self.parse_data)
        pass

    def parse_data(self, response):
        # parse_meta_data
        tags = ", ".join(response.css(".gallery-info .tags a span::text").getall())
        description = response.css(".title-section.gallery h1::text").get()
        for image_url in response.css(".gallery-ps4 .thumbwook a::attr(href)").getall():
            pair = ImageCaptionPairItem()
            pair['tags'] = tags
            pair['image_url'] = image_url
            pair['description'] = description
            yield pair
