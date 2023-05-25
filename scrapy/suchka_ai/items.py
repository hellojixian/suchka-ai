# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ImageCaptionPairItem(scrapy.Item):
    # define the fields for your item here like:
    description = scrapy.Field()
    url = scrapy.Field()
    tags = scrapy.Field()
    source = scrapy.Field()
    copyright = scrapy.Field()
    id = scrapy.Field()
    models = scrapy.Field()
    image_urls = scrapy.Field()

