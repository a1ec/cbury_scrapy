""" Run under bash with:
    timenow=`date +%Y%m%d_%H%M%S`; scrapy runspider cbury_spider.py -o cbury-scrape-$timenow.csv
    Problems? Interactively check Xpaths etc.:
    scrapy shell "http://datrack.canterbury.nsw.gov.au/cgi/datrack.pl?search=search&sortfield=^metadata.date_lodged"
"""
import scrapy
from cbury_scrapy.items import DA

def td_text_after(label, response):
    """ retrieves text from first td following a td containing a label e.g.:"""
    return response.xpath("//*[contains(text(), '" + label + "')]/following-sibling::td//text()").extract_first()

class CburySpider(scrapy.Spider):
    # scrapy.Spider attributes
    name = "cbury"
    allowed_domains = ["datrack.canterbury.nsw.gov.au"]
    start_urls = ["http://datrack.canterbury.nsw.gov.au/cgi/datrack.pl?search=search&sortfield=^metadata.date_lodged",]

    # required for unicode character replacement of '$' and ',' in est_cost
    translation_table = dict.fromkeys(map(ord, '$,'), None)
    da = DA()        
    da['lga'] = u"Canterbury"


    def parse(self, response):
        """ Retrieve DA no., URL and address for DA on summary list page """
        for row in response.xpath('//table/tr[@class="datrack_resultrow_odd" or @class="datrack_resultrow_even"]'):
            r = scrapy.Selector(text=row.extract(), type="html")
            self.da['da_no'] = r.xpath('//td[@class="datrack_danumber_cell"]//text()').extract_first()
            self.da['house_no'] = r.xpath('//td[@class="datrack_houseno_cell"]//text()').extract_first()
            self.da['street'] = r.xpath('//td[@class="datrack_street_cell"]//text()').extract_first()
            self.da['town'] = r.xpath('//td[@class="datrack_town_cell"]//text()').extract_first()
            self.da['url'] = r.xpath('//td[@class="datrack_danumber_cell"]//@href').extract_first()
            
            # then retrieve remaining DA details from the detail page
            yield scrapy.Request(self.da['url'], callback=self.parse_da_page)
                
        # follow next page link if one exists
        next_page = response.xpath("//*[contains(text(), 'Next')]/@href").extract_first()
        if next_page:
            yield scrapy.Request(next_page, self.parse)


    def parse_da_page(self, response):  
        """ Retrieve DA information from its detail page """        
        labels = { 'date_lodged': 'Date Lodged:', 'desc_full': 'Description:', 
                   'est_cost': 'Estimated Cost:', 'status': 'Status:',
                   'date_determined': 'Date Determined:', 'decision': 'Decision:',
                   'officer': 'Responsible Officer:' }
        
        # map DA fields with those in the following <td> elements on the page
        for i in labels:
            self.da[i] = td_text_after(labels[i], response)

        # convert est_cost text to int for easier sheet import "12,000" -> 12000
        if self.da['est_cost'] != None:
            self.da['est_cost'] = int(self.da['est_cost'].translate(self.translation_table))

        # Get people data from 'Names' table with 'Role' heading
        self.da['names'] = []
        for row in response.xpath('//table/tr[th[1]="Role"]/following-sibling::tr'):    
            da_name = {}
            da_name['role'] = row.xpath('normalize-space(./td[1])').extract_first()            
            da_name['name_no'] = row.xpath('normalize-space(./td[2])').extract_first()
            da_name['full_name'] = row.xpath('normalize-space(./td[3])').extract_first()
            self.da['names'].append(da_name)
                    
        yield self.da
