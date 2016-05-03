----
## A simple scrape app

> Using python to retrieve data from a government website.
> Scrapy python package is required to run the spider.
`
$ cd cbury_scrapy/cbury_scrapy/spider
$ timenow=date +%Y%m%d_%H%M%S;
$ scrapy runspider cbury_spider.py -o cbury-scrape-$timenow.json
`
> or csv suffix to output to CSV format.

> TODO
> Fix data integrity issue, rows are being output into file with incorrect 
> field values from other rows.
