----
## A simple scrape app

Retrieves data from a particular local government website.
Python and the Scrapy package is required to run the spider.

To run the spider and output JSON file, from bash:
      
    timenow=date +%Y%m%d_%H%M%S;
    scrapy runspider cbury_scrapy/spider/cbury_spider.py -o cbury-scrape-$timenow.json

Use the .csv suffix to output to CSV format instead.
