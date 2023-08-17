from urllib.parse import parse_qs, urlparse

import scrapy
from scrapy.loader import ItemLoader

from boatrace_crawler.items import RaceIndexItem


class BoatraceSpider(scrapy.Spider):
    name = "boatrace_spider"
    allowed_domains = ["www.boatrace.jp"]
    start_urls = ["https://www.boatrace.jp"]

    def __init__(self, start_url="https://www.boatrace.jp/owpc/pc/race/monthlyschedule?ym=202308", *args, **kwargs):
        super(BoatraceSpider, self).__init__(*args, **kwargs)

        self.start_urls = [start_url]

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
        if url.startswith("https://www.boatrace.jp/owpc/pc/race/monthlyschedule?"):
            self.logger.debug("#_follow: follow calendar page")
            return scrapy.Request(url, callback=self.parse_calendar, meta=meta)

        elif url.startswith("https://www.boatrace.jp/owpc/pc/race/raceindex?"):
            self.logger.debug("#_follow: follow race index page")
            return scrapy.Request(url, callback=self.parse_race_index, meta=meta)

        elif url.startswith("https://www.boatrace.jp/owpc/pc/race/racelist?"):
            self.logger.debug("#_follow: follow race program page")
            return scrapy.Request(url, callback=self.parse_race_program, meta=meta)

        else:
            raise Exception("Unknown url")

    def parse_calendar(self, response):
        """Parse calendar page.

        @url https://www.boatrace.jp/owpc/pc/race/monthlyschedule?ym=202308
        @returns items 0 0
        @returns requests 53 53
        @calendar_contract
        """
        self.logger.info(f"#parse_calendar: start: response={response.url}")

        # Parse link
        for a in response.xpath("//a"):
            race_index_url = urlparse(response.urljoin(a.xpath("@href").get()))
            race_index_qs = parse_qs(race_index_url.query)

            if race_index_url.path == "/owpc/pc/race/raceindex" and "jcd" in race_index_qs and "hd" in race_index_qs:
                self.logger.debug(f"#parse_calendar: a={race_index_url.geturl()}")

                race_index_url = f"https://www.boatrace.jp/owpc/pc/race/raceindex?jcd={race_index_qs['jcd'][0]}&hd={race_index_qs['hd'][0]}"
                yield self._follow(race_index_url)

    def parse_race_index(self, response):
        """Parse race index page.

        @url https://www.boatrace.jp/owpc/pc/race/raceindex?jcd=01&hd=20230731
        @returns items 1 1
        @returns requests 17
        @race_index_contract
        """
        self.logger.info(f"#parse_race_index: start: response={response.url}")

        # レースインデックスを構築する
        loader = ItemLoader(item=RaceIndexItem(type="RaceIndexItem"), response=response)

        race_index_url = urlparse(response.url)
        race_index_qs = parse_qs(race_index_url.query)
        loader.add_value("place_id", race_index_qs["jcd"][0])

        loader.add_xpath("place_name", "//div[@class='heading2_area']/img/@alt")

        loader.add_xpath("race_grade", "//div[@class='heading2_head']/div[2]/@class")

        loader.add_xpath("race_name", "//h2[@class='heading2_titleName']/text()")

        for a in response.xpath("//a[@class='tab2_inner']"):
            loader.add_value("race_index_urls", response.urljoin(a.xpath("@href").get()))
        loader.add_value("race_index_urls", response.url)

        item = loader.load_item()

        self.logger.debug(f"#parse_race_index: race_index={item}")
        yield item

        # 他の日をフォローする
        for a in response.xpath("//a[@class='tab2_inner']"):
            race_index_url = response.urljoin(a.xpath("@href").get())

            self.logger.debug(f"#parse_race_index: a={race_index_url}")

            yield self._follow(race_index_url)

        # レースラウンドをフォローする
        for a in response.xpath("//div[@class='table1']/table/tbody/tr/td[1]/a"):
            race_program_url = urlparse(response.urljoin(a.xpath("@href").get()))
            race_program_qs = parse_qs(race_program_url.query)

            if race_program_url.path == "/owpc/pc/race/racelist" and "rno" in race_program_qs and "jcd" in race_program_qs and "hd" in race_program_qs:
                self.logger.debug(f"#parse_race_index: a={race_program_url.geturl()}")

                race_program_url = f"https://www.boatrace.jp/owpc/pc/race/racelist?rno={race_program_qs['rno'][0]}&jcd={race_program_qs['jcd'][0]}&hd={race_program_qs['hd'][0]}"
                yield self._follow(race_program_url)

    def parse_race_program(self, response):
        """Parse race program page.

        @url https://www.boatrace.jp/owpc/pc/race/racelist?rno=1&jcd=01&hd=20230817
        """
        self.logger.info(f"#parse_race_program: start: response={response.url}")
