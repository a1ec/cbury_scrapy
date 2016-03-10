import scrapy

from scrapy.exceptions import CloseSpider
from cbury_scrapy.items import DA, DA_Person, Person

def td_text_after(label, response):
    """ retrieves text from first td following a td containing a label e.g.:"""
    return response.xpath("//*[contains(text(), '" + label + "')]/following-sibling::td//text()").extract_first()

class CburySpider(scrapy.Spider):
    name = "cbury"
    allowed_domains = ["datrack.canterbury.nsw.gov.au"]
    start_urls = [
        "http://datrack.canterbury.nsw.gov.au/cgi/datrack.pl?search=search&startidx=",
    ]

    url_index = 0
    MAX_URLS_TO_GET = 4
    URLS_PER_PAGE = 10
    
    records_remaining = MAX_URLS_TO_GET
    crawl_done = False
    
    da = DA()        
    da['lga'] = u"Canterbury"
        
    def parse(self, response):
        """ Start on search results page from index """ 
        # get number of total records
        self.num_records = int(response.xpath('//span[@class="datrack_count"]//text()').extract_first().split()[-1])
        
        while self.crawl_done != True:
            url = "http://datrack.canterbury.nsw.gov.au/cgi/datrack.pl?search=search&startidx=" + str(self.url_index)
            self.url_index += self.URLS_PER_PAGE

            yield scrapy.Request(url, callback=self.parse_da_results)
    
    
    def parse_da_results(self, response):
        """ Follow each DA link on DA list page """
        
        # extract and follow da href to get item details
        # Select all DA rows on the page
        for row in response.xpath('//table/tr[@class="datrack_resultrow_odd" or @class="datrack_resultrow_even"]'):


            r = scrapy.Selector(text=row.extract(), type="html")
            
            self.da['house_no'] = r.xpath('//td[@class="datrack_houseno_cell"]//text()').extract_first()
            self.da['street'] = r.xpath('//td[@class="datrack_street_cell"]//text()').extract_first()
            self.da['town'] = r.xpath('//td[@class="datrack_town_cell"]//text()').extract_first()
            
            url = r.xpath('//td[@class="datrack_danumber_cell"]//@href').extract_first()
            
            yield scrapy.Request(url, callback=self.parse_da_item)

            if self.records_remaining == 0:
                self.crawl_done = True
                #raise CloseSpider('Scraped requested number of records.')
            self.records_remaining -= 1
        
        
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
            da_p = {}
            da_p['role'] = row.xpath('normalize-space(./td[1])').extract_first()            
            da_p['name_no'] = row.xpath('normalize-space(./td[2])').extract_first()
            da_p['full_name'] = row.xpath('normalize-space(./td[3])').extract_first()
            self.da['names'].append(da_p)

        yield self.da
