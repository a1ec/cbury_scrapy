----
## A simple scrape app

Retrieves data from a particular local government website.
Python and the Scrapy package is required to run the spider.

Setup the python virtual environment with scrapy

    python3 -m venv venv
    source venv/bin/activate
    sudo apt update && sudo apt install -y python3-dev 
    pip install --upgrade pip scrapy


To run the spider and output JSON file, from bash:
      
    timenow=$(date +%Y%m%d_%H%M%S); \
    # Use the .csv suffix to output to CSV format instead.
    time scrapy runspider cbury_scrapy/spider/cbury_spider.py -o cbury-scrape-$timenow.json

