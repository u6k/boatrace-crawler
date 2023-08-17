import scrapy


class BoatraceSpiderSpider(scrapy.Spider):
    name = "boatrace_spider"
    allowed_domains = ["www.boatrace.jp"]
    start_urls = ["https://www.boatrace.jp"]

    def parse(self, response):
        pass
