----
## A simple scrape app

> Using python and scrapy to retrieve data from a government website.

> Run it with: timenow=`date +%Y%m%d_%H%M%S`;
               scrapy runspider cbury_spider.py -o cbury-scrape-$timenow.json

> TODO
> Fix data integrity issue, rows are being output into file with incorrect 
> field values from other rows.
