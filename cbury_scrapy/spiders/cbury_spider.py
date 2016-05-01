""" Run under bash like so
    timenow=`date +%Y%m%d_%H%M%S`; scrapy runspider cbury_spider.py -o cbury-scrape-$timenow.json
"""

import scrapy

from scrapy.exceptions import CloseSpider
from cbury_scrapy.items import DA, DA_Person, Person

def td_text_after(label, response):
    """ retrieves text from first td following a td containing a label e.g.:"""
    return response.xpath("//*[contains(text(), '" + label + "')]/following-sibling::td//text()").extract_first()

class CburySpider(scrapy.Spider):
    # scrapy.Spider attributes
    name = "cbury"
    allowed_domains = ["datrack.canterbury.nsw.gov.au"]
    start_urls = [
        "http://datrack.canterbury.nsw.gov.au/cgi/datrack.pl?search=search&sortfield=^metadata.date_lodged", # add &startidx=n if need be
    ]

    da = DA()        
    da['lga'] = u"Canterbury"
    # CloseSpider.CLOSESPIDER_ITEMCOUNT = MAX_ITEMS_TO_SCRAPE
    items_remaining = 0
            
    def parse(self, response):
        """ Retrieve total number of DAs from initial list page """ 
        # get number of total items
        self.items_remaining = int(response.xpath('//span[@class="datrack_count"]//text()').extract_first().split()[-1])
        self.logger.info('self.items_remaining = %d', self.items_remaining)
        yield scrapy.Request(response.url, self.parse_da_list)
    
    def parse_da_list(self, response):
        """ Retrieve DA information from the list page """
        # Select all DA rows on the page
        for row in response.xpath('//table/tr[@class="datrack_resultrow_odd" or @class="datrack_resultrow_even"]'):
            # Retrieve DA URL and address from the list page                
            r = scrapy.Selector(text=row.extract(), type="html")
            self.da['da_no'] = r.xpath('//td[@class="datrack_danumber_cell"]//text()').extract_first()
            self.da['house_no'] = r.xpath('//td[@class="datrack_houseno_cell"]//text()').extract_first()
            self.da['street'] = r.xpath('//td[@class="datrack_street_cell"]//text()').extract_first()
            self.da['town'] = r.xpath('//td[@class="datrack_town_cell"]//text()').extract_first()
            self.da['url'] = url = r.xpath('//td[@class="datrack_danumber_cell"]//@href').extract_first()
            
            #yield self.da
            # get the remaining DA details from its page
            yield scrapy.Request(url, callback=self.parse_da_item)
    
            self.items_remaining -= 1
            self.logger.info('self.items_remaining = %d', self.items_remaining)
        
            # terminate crawl if
            if self.items_remaining <= 0:
                raise CloseSpider("Scraped required number of items.")
                
        # follow next page link
        next_page = response.xpath("//*[contains(text(), 'Next')]/@href").extract_first()
        if next_page:
            yield scrapy.Request(next_page, self.parse_da_list)

    def parse_da_item(self, response):  
        """ Retrieve DA information from its page """
        self.da['url'] = response.url
        
        labels = { 'date_lodged': 'Date Lodged:', 'desc_full': 'Description:', 
                   'est_cost': 'Estimated Cost:', 'status': 'Status:',
                   'date_determined': 'Date Determined:', 'decision': 'Decision:',
                   'officer': 'Responsible Officer:'}
        
        # map DA fields with those in the folliwng <td> elements on the page
        for i in labels:
            self.da[i] = td_text_after(labels[i], response)

        # convert est_cost text to int for easier sheet import
        # e.g. "12,000,000" -> 12000000
        self.da[est_cost] = int(self.da[est_cost].translate(None, '$,'))

        # Get people data from 'Names' table, 'Role' heading
        self.da['names'] = []
        for row in response.xpath('//table/tr[th[1]="Role"]/following-sibling::tr'):    
            da_name = {}
            da_name['role'] = row.xpath('normalize-space(./td[1])').extract_first()            
            da_name['name_no'] = row.xpath('normalize-space(./td[2])').extract_first()
            da_name['full_name'] = row.xpath('normalize-space(./td[3])').extract_first()
            self.da['names'].append(da_name)
                    
        yield self.da
