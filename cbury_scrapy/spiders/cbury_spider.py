""" Run under bash like so
    timenow=`date +%Y%m%d_%H%M%S`;
    scrapy runspider cbury_spider.py -o ../../scraped_data/cbury-scrape-$timenow.csv
"""

import scrapy

from scrapy.exceptions import CloseSpider
from cbury_scrapy.items import DA, DA_Person, Person
from scrapy.shell import inspect_response

def td_text_after(label, response):
    """ retrieves text from first td following a td containing a label e.g.:"""
    return response.xpath("//*[contains(text(), '" + label + "')]/following-sibling::td//text()").extract_first()


class CburySpider(scrapy.Spider):
    # scrapy.Spider attributes
    name = "cbury"
    # required for unicode character replacement of '$' and ',' in est_cost
    translation_table = dict.fromkeys(map(ord, '$,'), None)

    allowed_domains = ["datrack.canterbury.nsw.gov.au"]
    start_urls = [
        "http://datrack.canterbury.nsw.gov.au/cgi/datrack.pl?search=search&sortfield=^metadata.date_lodged", # add &startidx=n if need be
    ]
    
    items_remaining = 0
    da = DA()        
    da['lga'] = u"Canterbury"
    # CloseSpider.CLOSESPIDER_ITEMCOUNT = 25

    def get_da_url_addr(self, response):
        # Select all DA rows on the page
        for row in response.xpath('//table/tr[@class="datrack_resultrow_odd" or @class="datrack_resultrow_even"]'):
            # Retrieve DA URL and address from the list page
            r = scrapy.Selector(text=row.extract(), type="html")
            self.da['da_no'] = r.xpath('//td[@class="datrack_danumber_cell"]//text()').extract_first()#
            self.da['house_no'] = r.xpath('//td[@class="datrack_houseno_cell"]//text()').extract_first()#
            self.da['street'] = r.xpath('//td[@class="datrack_street_cell"]//text()').extract_first()#
            self.da['town'] = r.xpath('//td[@class="datrack_town_cell"]//text()').extract_first()#
            self.da['url'] = url = r.xpath('//td[@class="datrack_danumber_cell"]//@href').extract_first()#
            
            # get the remaining DA details from its page
            yield scrapy.Request(self.da['url'], callback=self.parse_da_item)
    
    def parse(self, response):
        """ Retrieve total number of DAs from initial list page """ 
        # get number of total items
        self.items_remaining = int(response.xpath('//span[@class="datrack_count"]//text()').extract_first().split()[-1])
        self.logger.info('DAs found = %d', self.items_remaining)
        yield scrapy.Request(response.url, self.parse_da_list)
    
    def parse_da_list(self, response):
        """ Retrieve DA information from the list page """
        # get url and da
        self.get_da_url_addr(response)
        
        # invoke shell for inspection    
        # inspect_response(response, self)
                
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
                   'officer': 'Responsible Officer:' }
        
        # map DA fields with those in the folliwng <td> elements on the page
        for i in labels:
            self.da[i] = td_text_after(labels[i], response)

        # convert est_cost text to int for easier sheet import
        # e.g. "12,000,000" -> 12000000
        if self.da['est_cost'] != None:
            self.da['est_cost'] = int(self.da['est_cost'].translate(self.translation_table))

        # Get people data from 'Names' table, 'Role' heading
        self.da['names'] = []
        for row in response.xpath('//table/tr[th[1]="Role"]/following-sibling::tr'):    
            da_name = {}
            da_name['role'] = row.xpath('normalize-space(./td[1])').extract_first()            
            da_name['name_no'] = row.xpath('normalize-space(./td[2])').extract_first()
            da_name['full_name'] = row.xpath('normalize-space(./td[3])').extract_first()
            self.da['names'].append(da_name)
        
        yield self.da
