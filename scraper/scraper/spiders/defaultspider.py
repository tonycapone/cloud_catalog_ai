import scrapy
import json
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.exceptions import IgnoreRequest
from bs4 import BeautifulSoup
from scraper.items import ScraperItem

file = open("../cdk.context.json").read()
config = json.loads(file)


class DefaultSpider(CrawlSpider):
    name = 'defaultspider'
    allowed_domains = config["scrapeUrls"]
    start_urls = config["scrapeUrls"]
    
    # Define the rules for scraping and crawling.
    rules = (
        # Extract and follow links matching the pattern.
        # For each link followed, parse the response with parse_item.
        Rule(LinkExtractor(), callback='parse_item', follow=True, process_request='set_depth_limit'),
    )

    # This method sets the depth limit for each request.
    def set_depth_limit(self, request, spider):
        if 'depth' in request.meta and request.meta['depth'] > 2:
            raise IgnoreRequest("Ignoring request {}: depth limit reached".format(request))
        else:
            return request

    def parse_item(self, response):
        self.logger.info("Hi, this is an item page! %s", response.url)
        # extract data and store in variables
        item = ScraperItem()
        item['title'] = response.css('title::text').get()
        item['url'] = response.url
        content = response.xpath('//*[not(self::script or self::style)]/text()').getall()

        # use BeautifulSoup to parse and clean up the HTML
        soup = BeautifulSoup(' '.join(content), 'html.parser')
        content_data = soup.get_text(separator=' ')
        item['content'] = content_data
        self.logger.info(item)

        # yield the data
        return item
    
