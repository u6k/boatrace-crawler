from urllib.parse import parse_qs, urlparse

import scrapy
from scrapy.loader import ItemLoader

from boatrace_crawler.items import OddsItem


class OrangebuoySpider(scrapy.Spider):
    name = "orangebuoy_spider"
    allowed_domains = ["www.orangebuoy.net"]
    start_urls = ["http://www.orangebuoy.net/odds/?year=2023&month=10"]

    def __init__(self, start_url="http://www.orangebuoy.net/odds/?year=2023&month=10", *args, **kwargs):
        super(OrangebuoySpider, self).__init__(*args, **kwargs)

        self.start_urls = [start_url]

    def start_requests(self):
        for url in self.start_urls:
            yield self._follow(url)

    def parse(self, response):
        """Parse start_url."""
        self.logger.info(f"#parse: start: response={response.url}")

        yield self._follow(self.start_urls[0])

    def _follow(self, url):
        self.logger.debug(f"#_follow: start: url={url}")

        # Setting http proxy
        meta = {}
        if self.settings["CRAWL_HTTP_PROXY"]:
            meta["proxy"] = self.settings["CRAWL_HTTP_PROXY"]
        self.logger.debug(f"#_follow: start: meta={meta}")

        # Build request
        url_parsed = urlparse(url)
        url_qs = parse_qs(url_parsed.query)

        if url_parsed.path == "/odds/" and "year" in url_qs and "month" in url_qs and "day" in url_qs and "jyo" in url_qs and "r" in url_qs and "mode" in url_qs:
            self.logger.debug("#_follow: follow odds page")
            return scrapy.Request(url, callback=self.parse_odds, meta=meta)

        elif url_parsed.path == "/odds/" and "year" in url_qs and "month" in url_qs and "day" in url_qs and "jyo" in url_qs:
            self.logger.debug("#_follow: follow place page")
            return scrapy.Request(url, callback=self.parse_place, meta=meta)

        elif url_parsed.path == "/odds/" and "year" in url_qs and "month" in url_qs and "day" in url_qs:
            self.logger.debug("#_follow: follow day page")
            return scrapy.Request(url, callback=self.parse_day, meta=meta)

        elif url_parsed.path == "/odds/" and "year" in url_qs and "month" in url_qs:
            self.logger.debug("#_follow: follow month page")
            return scrapy.Request(url, callback=self.parse_month, meta=meta)

        else:
            raise Exception(f"Unknown url: {url}")

    def parse_month(self, response):
        """Parse month page.

        @url http://www.orangebuoy.net/odds/?year=2023&month=10
        @returns items 0 0
        @returns requests 31 31
        @orangebuoy_month_contract
        """
        self.logger.info(f"#parse_month: start: response={response.url}")

        # Parse link
        for a in response.xpath("//a"):
            url = urlparse(response.urljoin(a.xpath("@href").get()))
            qs = parse_qs(url.query)

            if url.path == "/odds/" and "year" in qs and "month" in qs and "day" in qs:
                self.logger.debug(f"#parse_month: a={url.geturl()}")

                url_day = f"http://www.orangebuoy.net/odds/?year={qs['year'][0]}&month={qs['month'][0]}&day={qs['day'][0]}"
                yield self._follow(url_day)

    def parse_day(self, response):
        """Parse day page.

        @url http://www.orangebuoy.net/odds/?year=2023&month=10&day=30
        @returns items 0 0
        @returns requests 9 9
        @orangebuoy_day_contract
        """
        self.logger.info(f"#parse_day: start: response={response.url}")

        # Parse link
        for a in response.xpath("//a"):
            url = urlparse(response.urljoin(a.xpath("@href").get()))
            qs = parse_qs(url.query)

            if url.path == "/odds/" and "year" in qs and "month" in qs and "day" in qs and "jyo" in qs:
                self.logger.debug(f"#parse_month: a={url.geturl()}")

                url_place = f"http://www.orangebuoy.net/odds/?year={qs['year'][0]}&month={qs['month'][0]}&day={qs['day'][0]}&jyo={qs['jyo'][0]}"
                yield self._follow(url_place)

    def parse_place(self, response):
        """Parse place page.

        @url http://www.orangebuoy.net/odds/?year=2023&month=10&day=30&jyo=2
        @returns items 0 0
        @returns requests 60 60
        @orangebuoy_place_contract
        """
        self.logger.info(f"#parse_place: start: response={response.url}")

        # Parse link
        for a in response.xpath("//a"):
            url = urlparse(response.urljoin(a.xpath("@href").get()))
            qs = parse_qs(url.query)

            if url.path == "/odds/" and "year" in qs and "month" in qs and "day" in qs and "jyo" in qs and "r" in qs:
                self.logger.debug(f"#parse_month: a={url.geturl()}")

                for m in [1, 2, 3, 4, 5]:
                    url_odds = f"http://www.orangebuoy.net/odds/?year={qs['year'][0]}&month={qs['month'][0]}&day={qs['day'][0]}&jyo={qs['jyo'][0]}&r={qs['r'][0]}&mode={m}"
                    yield self._follow(url_odds)

    def parse_odds(self, response):
        """Parse odds page.

        @url http://www.orangebuoy.net/odds/?year=2023&month=10&day=30&jyo=2&r=12&mode=5
        @returns items 185 185
        @returns requests 0 0
        @orangebuoy_odds_contract
        """
        self.logger.info(f"#parse_odds: start: response={response.url}")

        for t in response.xpath("//div[@class='waku']/table"):
            table_title = t.xpath("following-sibling::b/text()").get()
            table = t.xpath("tr/td/div[@class='oddstable']/table")

            if table_title == "2連単":
                # 3連単
                for i in range(6):
                    bracket_number_1 = table.xpath(f"tr[1]/td[{i*2+1}]/text()").get()

                    for j in range(5):
                        bracket_number_2 = table.xpath(f"tr[{j*4+2}]/td[{i*3+1}]/text()").get()

                        for k in range(4):
                            if k == 0:
                                bracket_number_3 = table.xpath(f"tr[{j*4+k+2}]/td[{i*3+2}]/text()").get()
                                odds = table.xpath(f"tr[{j*4+k+2}]/td[{i*3+3}]/descendant-or-self::text()").get()
                            else:
                                bracket_number_3 = table.xpath(f"tr[{j*4+k+2}]/td[{i*2+1}]/text()").get()
                                odds = table.xpath(f"tr[{j*4+k+2}]/td[{i*2+2}]/descendant-or-self::text()").get()

                            loader = ItemLoader(item=OddsItem(), selector=None)
                            loader.add_value("url", response.url + "#odds_3t")
                            loader.add_value("bracket_number_1", bracket_number_1)
                            loader.add_value("bracket_number_2", bracket_number_2)
                            loader.add_value("bracket_number_3", bracket_number_3)
                            loader.add_value("odds", odds)

                            item = loader.load_item()

                            self.logger.debug(f"#parse_odds: odds={item}")
                            yield item

            elif table_title == "3連複":
                # 2連単
                for i in range(6):
                    for j in range(5):
                        loader = ItemLoader(item=OddsItem(), selector=table)
                        loader.add_value("url", response.url + "#odds_2t")
                        loader.add_xpath("bracket_number_1", f"tr[1]/td[{i*3+1}]/text()")

                        if j == 0:
                            loader.add_xpath("bracket_number_2", f"tr[{j+1}]/td[{i*3+2}]/text()")
                            loader.add_xpath("odds", f"tr[{j+1}]/td[{i*3+3}]/descendant-or-self::text()")
                        else:
                            loader.add_xpath("bracket_number_2", f"tr[{j+1}]/td[{i*2+1}]/text()")
                            loader.add_xpath("odds", f"tr[{j+1}]/td[{i*2+2}]/descendant-or-self::text()")

                        item = loader.load_item()

                        self.logger.debug(f"#parse_odds: odds={item}")
                        yield item

            elif table_title == "2連複":
                # 3連複
                for i in range(5):
                    for j in range(4):
                        loader = ItemLoader(item=OddsItem(), selector=table)
                        loader.add_value("url", response.url + "#odds_3f")
                        loader.add_xpath("bracket_number_1", f"tr[{j+1}]/td[{i*4+1}]/text()")
                        loader.add_xpath("bracket_number_2", f"tr[{j+1}]/td[{i*4+2}]/text()")
                        loader.add_xpath("bracket_number_3", f"tr[{j+1}]/td[{i*4+3}]/text()")
                        loader.add_xpath("odds", f"tr[{j+1}]/td[{i*4+4}]/descendant-or-self::text()")

                        item = loader.load_item()

                        self.logger.debug(f"#parse_odds: odds={item}")
                        yield item

            elif table_title == "結果":
                # 2連複
                for y in range(5):
                    for x in range(y + 1):
                        loader = ItemLoader(item=OddsItem(), selector=table)
                        loader.add_value("url", response.url + "#odds_2f")
                        loader.add_xpath("bracket_number_1", f"tr[{y+1}]/td[{x*3+1}]/text()")
                        loader.add_xpath("bracket_number_2", f"tr[{y+1}]/td[{x*3+2}]/text()")
                        loader.add_xpath("odds", f"tr[{y+1}]/td[{x*3+3}]/descendant-or-self::text()")

                        item = loader.load_item()

                        self.logger.debug(f"#parse_odds: odds={item}")
                        yield item
