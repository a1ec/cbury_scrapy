# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class DA(scrapy.Item):
    da_no = scrapy.Field()
    lga = scrapy.Field()
    url = scrapy.Field()
    date_lodged = scrapy.Field()

    house_no = scrapy.Field()
    street = scrapy.Field()
    town = scrapy.Field()
    
    desc_full = scrapy.Field()
    est_cost = scrapy.Field()
    status = scrapy.Field()
    
    names = scrapy.Field()
    officer = scrapy.Field()
    date_determined = scrapy.Field()
    decision = scrapy.Field()
    
    date_scr_created = scrapy.Field()
    date_scr_modified = scrapy.Field()
    
    # TODO properties list: property_no

class DA_Person(scrapy.Item):
    name_no = scrapy.Field()
    full_name = scrapy.Field()
    role = scrapy.Field()

class Person(scrapy.Item):
    name_no = scrapy.Field()
    full_name = scrapy.Field()
    
class Property(scrapy.Item):
    property_no = scrapy.Field()
    full_address = scrapy.Field()
