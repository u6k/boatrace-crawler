from urllib.parse import parse_qs, urlparse

import scrapy


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

        @url https://www.boatrace.jp/owpc/pc/race/raceindex?jcd=01&hd=20230803
        """
        self.logger.info(f"#parse_race_index: start: response={response.url}")
