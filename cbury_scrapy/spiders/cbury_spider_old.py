import scrapy

from scrapy.exceptions import CloseSpider, IgnoreRequest
from cbury_scrapy.items import DA, DA_Person, Person

def td_text_after(label, response):
    """ retrieves text from first td following a td containing a label e.g.:"""
    return response.xpath("//*[contains(text(), '" + label + "')]/following-sibling::td//text()").extract_first()

class CburySpider(scrapy.Spider):
    # Run under bash like so
    # timenow=`date +%Y%m%d_%H%M%S`; scrapy runspider cbury_spider.py -o cbury-scrape-$timenow.json
    NUM_ITEMS_TO_SCRAPE = 12
    ITEMS_PER_RESULTS_PAGE = 10

    # CloseSpider.CLOSESPIDER_ITEMCOUNT = MAX_ITEMS_TO_SCRAPE
    items_remaining = NUM_ITEMS_TO_SCRAPE
    crawl_done = False
    num_items = 0

    results_index = 0

    # scrapy.Spider attributes
    name = "cbury"
    allowed_domains = ["datrack.canterbury.nsw.gov.au"]
    start_urls = [
        "http://datrack.canterbury.nsw.gov.au/cgi/datrack.pl?search=search&startidx=" + str(results_index),
    ]

    da = DA()        
    da['lga'] = u"Canterbury"

    def parse(self, response):
        """ Begin parsing DA list page from index supplied """ 
        # get number of total items
        self.num_items = int(response.xpath('//span[@class="datrack_count"]//text()').extract_first().split()[-1])
        
        #self.logger.info('Parse function called on %s', response.url)
        #self.logger.info('Total items = %d', self.num_items)
        
        url = "http://datrack.canterbury.nsw.gov.au/cgi/datrack.pl?search=search&startidx=" + str(self.results_index)
        self.results_index += self.ITEMS_PER_RESULTS_PAGE # offset url index to next page
        yield scrapy.Request(url, callback=self.parse_da_list)

    def parse_da_list(self, response):
        """ Follow each DA link on DA list page """        

        # Select all DA rows on the page
        for row in response.xpath('//table/tr[@class="datrack_resultrow_odd" or @class="datrack_resultrow_even"]'):
            if self.crawl_done == True:
                
                raise CloseSpider('Scraped requested number of items.')
                # added as CloseSpider is not responsive
                raise IgnoreRequest()
                return
            # Retrieve DA URL and address from the list page                
            r = scrapy.Selector(text=row.extract(), type="html")
            self.da['house_no'] = r.xpath('//td[@class="datrack_houseno_cell"]//text()').extract_first()
            self.da['street'] = r.xpath('//td[@class="datrack_street_cell"]//text()').extract_first()
            self.da['town'] = r.xpath('//td[@class="datrack_town_cell"]//text()').extract_first()
            url = r.xpath('//td[@class="datrack_danumber_cell"]//@href').extract_first()

            # follow URL link for further DA details
            yield scrapy.Request(url, callback=self.parse_da_item)
            
        
    def parse_da_item(self, response):  
        """ Parse individual DA fields """
        self.da['url'] = response.url
        
        labels = { 'da_no': 'Application No:', 'date_lodged': 'Date Lodged:',
                   'desc_full': 'Description:', 'est_cost': 'Estimated Cost:',
                   'status': 'Status:', 'date_determined': 'Date Determined:', 
                   'decision': 'Decision:', 'officer': 'Responsible Officer:'}
        
        # map DA fields with those in the folliwng <td> elements on the page
        for i in labels:
            self.da[i] = td_text_after(labels[i], response)

        # Get people data from 'Names' table, 'Role' heading
        self.da['names'] = []
        for row in response.xpath('//table/tr[th[1]="Role"]/following-sibling::tr'):    
            da_name = {}
            da_name['role'] = row.xpath('normalize-space(./td[1])').extract_first()            
            da_name['name_no'] = row.xpath('normalize-space(./td[2])').extract_first()
            da_name['full_name'] = row.xpath('normalize-space(./td[3])').extract_first()
            self.da['names'].append(da_name)

        self.items_remaining -= 1
        self.logger.info('self.items_remaining = %d', self.items_remaining)
        
        if self.items_remaining <= 0:
            self.crawl_done = True
        
        yield self.da
