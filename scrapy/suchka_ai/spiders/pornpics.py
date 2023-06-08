import scrapy
import re
import os
from ..items import ImageCaptionPairItem
from scrapy.loader import ItemLoader

class PornpicsSpider(scrapy.Spider):
    name = "pornpics"
    allowed_domains = ["pornpics.com"]
    start_urls = ["https://www.pornpics.com/channels/list/0-9/"]

    def parse(self, response):
        if response.url in self.start_urls:
            yield from self.parse_channel_list(response)

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

        for link in response.css("#content .alphabet .alpha a::attr(href)").getall()[1:]:
            yield response.follow(link, callback=self.parse_channel_list)

    def parse_data_list(self, response):
        for data in response.json():
            data_url = data['g_url']
            if self.is_duplicated(data['gid']): continue
            yield scrapy.Request(data_url, callback=self.parse_data)

    def parse_data(self, response):
        # parse_meta_data
        tags = ", ".join(response.css(".gallery-info .tags a span::text").getall())
        description = response.css(".title-section.gallery h1::text").get()
        models = ", ".join(response.css(".gallery-info .gallery-info__item:nth-child(2) a span::text").getall())
        copyright =  ", ".join(response.css(".gallery-info__item a::text").getall())
        image_urls = response.css(".gallery-ps4 .thumbwook a::attr(href)").getall()
        pair = ImageCaptionPairItem()
        pair['id'] = re.search(r"var ID\s+=\s+'([0-9]+)'",response.text).group(1)
        if self.is_duplicated(pair['id']): return
        pair['source'] = self.name
        pair['models'] = models
        pair['copyright'] = copyright
        pair['tags'] = tags
        pair['url'] = response.url
        pair['image_urls'] = image_urls
        pair['description'] = description
        yield pair

    def is_duplicated(self, id):
        data_path = os.path.join(self.settings.get('IMAGES_STORE'), self.name, id, 'data.json')
        return os.path.exists(data_path)