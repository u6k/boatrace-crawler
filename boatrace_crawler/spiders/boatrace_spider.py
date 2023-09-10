from urllib.parse import parse_qs, urlparse

import scrapy
from scrapy.loader import ItemLoader

from boatrace_crawler.items import OddsItem, RaceIndexItem, RaceProgramBracketItem, RaceProgramBracketResultsItem, RaceProgramItem, RaceResultPayoffItem, RaceResultStartTimeItem, RaceResultTimeItem, RacerItem


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

        elif url.startswith("https://www.boatrace.jp/owpc/pc/race/odds3t?"):
            self.logger.debug("#_follow: follow odds 3t page")
            return scrapy.Request(url, callback=self.parse_odds_3t, meta=meta)

        elif url.startswith("https://www.boatrace.jp/owpc/pc/race/odds3f?"):
            self.logger.debug("#_follow: follow odds 3f page")
            return scrapy.Request(url, callback=self.parse_odds_3f, meta=meta)

        elif url.startswith("https://www.boatrace.jp/owpc/pc/race/odds2tf?"):
            self.logger.debug("#_follow: follow odds 2tf page")
            return scrapy.Request(url, callback=self.parse_odds_2tf, meta=meta)

        elif url.startswith("https://www.boatrace.jp/owpc/pc/race/oddsk?"):
            self.logger.debug("#_follow: follow odds k page")
            return scrapy.Request(url, callback=self.parse_odds_k, meta=meta)

        elif url.startswith("https://www.boatrace.jp/owpc/pc/race/oddstf?"):
            self.logger.debug("#_follow: follow odds tf page")
            return scrapy.Request(url, callback=self.parse_odds_tf, meta=meta)

        elif url.startswith("https://www.boatrace.jp/owpc/pc/race/raceresult?"):
            self.logger.debug("#_follow: follow race result page")
            return scrapy.Request(url, callback=self.parse_race_result, meta=meta)

        elif url.startswith("https://www.boatrace.jp/owpc/pc/data/racersearch/profile?"):
            self.logger.debug("#_follow: follow racer profile page")
            return scrapy.Request(url, callback=self.parse_racer_profile, meta=meta)

        else:
            raise Exception("Unknown url")

    def parse_calendar(self, response):
        """Parse calendar page.

        @url https://www.boatrace.jp/owpc/pc/race/monthlyschedule?ym=202307
        @returns items 0 0
        @returns requests 81 81
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
        @returns requests 17 17
        @race_index_contract
        """
        self.logger.info(f"#parse_race_index: start: response={response.url}")

        # レースインデックスを構築する
        loader = ItemLoader(item=RaceIndexItem(), response=response)
        loader.add_value("url", response.url)

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

        @url https://www.boatrace.jp/owpc/pc/race/racelist?rno=5&jcd=01&hd=20230817
        @returns items 49 49
        @returns requests 12 12
        @race_program_contract
        """
        self.logger.info(f"#parse_race_program: start: response={response.url}")

        race_program_url = urlparse(response.url)
        race_program_qs = parse_qs(race_program_url.query)

        #
        # レース出走表を構築する
        #
        loader = ItemLoader(item=RaceProgramItem(), response=response)
        loader.add_value("url", response.url + "#info")
        loader.add_xpath("course_length", "translate(normalize-space(//h3[@class='title16_titleDetail__add2020']), ' ', '')")

        # 出走時刻を抽出する
        race_round_classes = []
        for th in response.xpath("//div[@class='table1 h-mt10']/table/thead/tr/th"):
            race_round_classes.append(th.xpath("@class").get())

        start_times = []
        for td in response.xpath("//div[@class='table1 h-mt10']/table/tbody/tr/td"):
            start_times.append(td.xpath("text()").get())

        for race_round_class, start_time in zip(race_round_classes, start_times):
            if race_round_class is None:
                loader.add_value("start_time", start_time)

        item = loader.load_item()

        self.logger.debug(f"#parse_race_program: race_program={item}")
        yield item

        #
        # ボートレーサーを構築する
        #
        for tbody in response.xpath("//div[@class='table1 is-tableFixed__3rdadd']/table/tbody"):
            loader = ItemLoader(item=RaceProgramBracketItem(), selector=tbody)

            loader.add_value("url", response.url + "#bracket")
            loader.add_xpath("bracket_number", "tr[1]/td[1]/text()")
            loader.add_xpath("racer_data1", "translate(normalize-space(tr[1]/td[3]/div[1]), ' ', '')")
            loader.add_xpath("racer_data2", "translate(normalize-space(tr[1]/td[3]/div[3]), ' ', '/')")
            loader.add_xpath("racer_data3", "translate(normalize-space(tr[1]/td[4]), ' ', '/')")
            loader.add_xpath("racer_rate_all_place", "translate(normalize-space(tr[1]/td[5]), ' ', '/')")
            loader.add_xpath("racer_rate_current_place", "translate(normalize-space(tr[1]/td[6]), ' ', '/')")
            loader.add_xpath("motor_rate", "translate(normalize-space(tr[1]/td[7]), ' ', '/')")
            loader.add_xpath("boat_rate", "translate(normalize-space(tr[1]/td[8]), ' ', '/')")

            item = loader.load_item()

            self.logger.debug(f"#parse_race_program: race_program_bracket={item}")
            yield item

            #
            # 今節成績を構築する
            #
            for i in range(14):
                loader = ItemLoader(item=RaceProgramBracketResultsItem(), selector=tbody)
                loader.add_value("url", response.url + "#bracket_result")
                loader.add_xpath("bracket_number", "tr[1]/td[1]/text()")
                loader.add_value("run_number", i)
                loader.add_xpath("bracket_color", f"tr[1]/td[{i+10}]/@class")
                loader.add_xpath("race_round", f"tr[1]/td[{i+10}]/text()")
                loader.add_xpath("approach_course", f"tr[2]/td[{i+1}]/text()")
                loader.add_xpath("start_timing", f"tr[3]/td[{i+1}]/text()")
                loader.add_xpath("result", f"tr[4]/td[{i+1}]/a/text()")

                item = loader.load_item()

                if item["race_round"][0] == "\xa0":
                    # 空データの場合、読み飛ばす
                    continue

                self.logger.debug(f"#parse_race_program: race_program_bracket_result={item}")
                yield item

        #
        # リンクを解析する
        #

        # オッズ
        odds_url = response.urljoin(f"/owpc/pc/race/odds3t?rno={race_program_qs['rno'][0]}&jcd={race_program_qs['jcd'][0]}&hd={race_program_qs['hd'][0]}")
        self.logger.debug(f"#parse_race_program: a={odds_url}")
        yield self._follow(odds_url)

        odds_url = response.urljoin(f"/owpc/pc/race/odds3f?rno={race_program_qs['rno'][0]}&jcd={race_program_qs['jcd'][0]}&hd={race_program_qs['hd'][0]}")
        self.logger.debug(f"#parse_race_program: a={odds_url}")
        yield self._follow(odds_url)

        odds_url = response.urljoin(f"/owpc/pc/race/odds2tf?rno={race_program_qs['rno'][0]}&jcd={race_program_qs['jcd'][0]}&hd={race_program_qs['hd'][0]}")
        self.logger.debug(f"#parse_race_program: a={odds_url}")
        yield self._follow(odds_url)

        odds_url = response.urljoin(f"/owpc/pc/race/oddsk?rno={race_program_qs['rno'][0]}&jcd={race_program_qs['jcd'][0]}&hd={race_program_qs['hd'][0]}")
        self.logger.debug(f"#parse_race_program: a={odds_url}")
        yield self._follow(odds_url)

        odds_url = response.urljoin(f"/owpc/pc/race/oddstf?rno={race_program_qs['rno'][0]}&jcd={race_program_qs['jcd'][0]}&hd={race_program_qs['hd'][0]}")
        self.logger.debug(f"#parse_race_program: a={odds_url}")
        yield self._follow(odds_url)

        # 結果
        result_url = response.urljoin(f"/owpc/pc/race/raceresult?rno={race_program_qs['rno'][0]}&jcd={race_program_qs['jcd'][0]}&hd={race_program_qs['hd'][0]}")
        self.logger.debug(f"#parse_race_program: a={result_url}")
        yield self._follow(result_url)

        # レーサー
        for a in response.xpath("//div[@class='table1 is-tableFixed__3rdadd']/table/tbody/tr/td[3]//a"):
            profile_url = urlparse(response.urljoin(a.xpath("@href").get()))

            if profile_url.path == "/owpc/pc/data/racersearch/profile":
                self.logger.debug(f"#parse_race_program: a={profile_url.geturl()}")
                yield self._follow((profile_url.geturl()))

    def parse_odds_3t(self, response):
        """Parse odds 3t page.

        @url https://www.boatrace.jp/owpc/pc/race/odds3t?rno=5&jcd=01&hd=20230817
        @returns items 120 120
        @returns requests 0 0
        @odds_3t_contract
        """
        self.logger.info(f"#parse_odds_3t: start: response={response.url}")

        if response.xpath("//h3[contains(@class, 'title12_title') and contains(text(), 'データはありません。')]"):
            # データがない場合は処理を戻す
            self.logger.debug("#parse_odds_3t: no data")
            return

        table = response.xpath("//div[@class='table1']/table")

        for i in range(6):
            bracket_number_1 = table.xpath(f"thead/tr/th[{i*2+1}]/text()").get()

            for j in range(5):
                bracket_number_2 = table.xpath(f"tbody/tr[{j*4+1}]/td[{i*3+1}]/text()").get()

                for k in range(4):
                    if k == 0:
                        bracket_number_3 = table.xpath(f"tbody/tr[{j*4+k+1}]/td[{i*3+2}]/text()").get()
                        odds = table.xpath(f"tbody/tr[{j*4+k+1}]/td[{i*3+3}]/text()").get()
                    else:
                        bracket_number_3 = table.xpath(f"tbody/tr[{j*4+k+1}]/td[{i*2+1}]/text()").get()
                        odds = table.xpath(f"tbody/tr[{j*4+k+1}]/td[{i*2+2}]/text()").get()

                    loader = ItemLoader(item=OddsItem(), selector=None)
                    loader.add_value("url", response.url)
                    loader.add_value("bracket_number_1", bracket_number_1)
                    loader.add_value("bracket_number_2", bracket_number_2)
                    loader.add_value("bracket_number_3", bracket_number_3)
                    loader.add_value("odds", odds)

                    item = loader.load_item()

                    self.logger.debug(f"#parse_odds_3t: odds={item}")
                    yield item

    def parse_odds_3f(self, response):
        """Parse odds 3f page.

        @url https://www.boatrace.jp/owpc/pc/race/odds3f?rno=5&jcd=01&hd=20230817
        @returns items 20 20
        @returns requests 0 0
        @odds_3f_contract
        """
        self.logger.info(f"#parse_odds_3f: start: response={response.url}")

        table = response.xpath("//div[@class='table1']/table")

        def load_odds_item(bracket_number_1, bracket_number_2, bracket_number_3, table_row, table_col):
            odds = table.xpath(f"tbody/tr[{table_row}]/td[{table_col}]/text()").get()

            loader = ItemLoader(item=OddsItem(), selector=None)
            loader.add_value("url", response.url)
            loader.add_value("bracket_number_1", bracket_number_1)
            loader.add_value("bracket_number_2", bracket_number_2)
            loader.add_value("bracket_number_3", bracket_number_3)
            loader.add_value("odds", odds)

            item = loader.load_item()

            self.logger.debug(f"#parse_odds_3f: odds={item}")
            return item

        yield load_odds_item(1, 2, 3, 1, 3)
        yield load_odds_item(1, 2, 4, 2, 2)
        yield load_odds_item(1, 2, 5, 3, 2)
        yield load_odds_item(1, 2, 6, 4, 2)
        yield load_odds_item(1, 3, 4, 5, 3)
        yield load_odds_item(1, 3, 5, 6, 2)
        yield load_odds_item(1, 3, 6, 7, 2)
        yield load_odds_item(1, 4, 5, 8, 3)
        yield load_odds_item(1, 4, 6, 9, 2)
        yield load_odds_item(1, 5, 6, 10, 3)
        yield load_odds_item(2, 3, 4, 5, 3)
        yield load_odds_item(2, 3, 5, 6, 2)
        yield load_odds_item(2, 3, 6, 7, 2)
        yield load_odds_item(2, 4, 5, 8, 3)
        yield load_odds_item(2, 4, 6, 9, 2)
        yield load_odds_item(2, 5, 6, 10, 3)
        yield load_odds_item(3, 4, 5, 8, 3)
        yield load_odds_item(3, 4, 6, 9, 2)
        yield load_odds_item(3, 5, 6, 10, 3)
        yield load_odds_item(4, 5, 6, 10, 3)

    def parse_odds_2tf(self, response):
        """Parse odds 2tf page.

        @url https://www.boatrace.jp/owpc/pc/race/odds2tf?rno=5&jcd=01&hd=20230817
        @returns items 45 45
        @returns requests 0 0
        @odds_2tf_contract
        """
        self.logger.info(f"#parse_odds_2tf: start: response={response.url}")

        # 2連単オッズをパースする
        table = response.xpath("//div[@class='table1'][1]/table")

        for i in range(6):
            for j in range(5):
                loader = ItemLoader(item=OddsItem(), selector=table)
                loader.add_value("url", response.url + "#odds2t")
                loader.add_xpath("bracket_number_1", f"thead/tr/th[{i*2+1}]/text()")
                loader.add_xpath("bracket_number_2", f"tbody/tr[{j+1}]/td[{i*2+1}]/text()")
                loader.add_xpath("odds", f"tbody/tr[{j+1}]/td[{i*2+2}]/text()")

                item = loader.load_item()

                self.logger.debug(f"#parse_odds_2tf: odds={item}")
                yield item

        # 2連複オッズをパースする
        table = response.xpath("//div[@class='table1'][2]/table")

        for i in range(6):
            for j in range(5):
                loader = ItemLoader(item=OddsItem(), selector=table)
                loader.add_value("url", response.url + "#odds2f")
                loader.add_xpath("bracket_number_1", f"thead/tr/th[{i*2+1}]/text()")
                loader.add_xpath("bracket_number_2", f"tbody/tr[{j+1}]/td[{i*2+1}]/text()")
                loader.add_xpath("odds", f"tbody/tr[{j+1}]/td[{i*2+2}]/text()")

                item = loader.load_item()

                if len(item["bracket_number_2"][0].strip()) == 0:
                    # 空データの場合、読み飛ばす
                    continue

                self.logger.debug(f"#parse_odds_2tf: odds={item}")
                yield item

    def parse_odds_k(self, response):
        """Parse odds k page.

        @url https://www.boatrace.jp/owpc/pc/race/oddsk?rno=5&jcd=01&hd=20230817
        @returns items 15 15
        @returns requests 0 0
        @odds_k_contract
        """
        self.logger.info(f"#parse_odds_k: start: response={response.url}")

        table = response.xpath("//div[@class='table1'][1]/table")

        for i in range(6):
            for j in range(5):
                loader = ItemLoader(item=OddsItem(), selector=table)
                loader.add_value("url", response.url)
                loader.add_xpath("bracket_number_1", f"thead/tr/th[{i*2+1}]/text()")
                loader.add_xpath("bracket_number_2", f"tbody/tr[{j+1}]/td[{i*2+1}]/text()")
                loader.add_xpath("odds", f"tbody/tr[{j+1}]/td[{i*2+2}]/text()")

                item = loader.load_item()

                if len(item["bracket_number_2"][0].strip()) == 0:
                    # 空データの場合、読み飛ばす
                    continue

                self.logger.debug(f"#parse_odds_k: odds={item}")
                yield item

    def parse_odds_tf(self, response):
        """Parse odds tf page.

        @url https://www.boatrace.jp/owpc/pc/race/oddstf?rno=5&jcd=01&hd=20230817
        @returns items 12 12
        @returns requests 0 0
        @odds_tf_contract
        """
        self.logger.info(f"#parse_odds_tf: start: response={response.url}")

        # 単勝オッズをパースする
        table = response.xpath("//div[@class='grid_unit'][1]/div[@class='table1']/table")

        for i in range(6):
            loader = ItemLoader(item=OddsItem(), selector=table)
            loader.add_value("url", response.url + "#oddst")
            loader.add_xpath("bracket_number_1", f"tbody[{i+1}]/tr/td[1]/text()")
            loader.add_xpath("odds", f"tbody[{i+1}]/tr/td[3]/text()")

            item = loader.load_item()

            self.logger.debug(f"#parse_odds_tf: odds={item}")
            yield item

        # 複勝オッズをパースする
        table = response.xpath("//div[@class='grid_unit'][2]/div[@class='table1']/table")

        for i in range(6):
            loader = ItemLoader(item=OddsItem(), selector=table)
            loader.add_value("url", response.url + "#oddsf")
            loader.add_xpath("bracket_number_1", f"tbody[{i+1}]/tr/td[1]/text()")
            loader.add_xpath("odds", f"tbody[{i+1}]/tr/td[3]/text()")

            item = loader.load_item()

            self.logger.debug(f"#parse_odds_tf: odds={item}")
            yield item

    def parse_race_result(self, response):
        """Parse race result page.

        @url https://www.boatrace.jp/owpc/pc/race/raceresult?rno=5&jcd=01&hd=20230817
        @returns items 22 22
        @returns requests 0 0
        @race_result_contract
        """
        self.logger.info(f"#parse_race_result: start: response={response.url}")

        # 着順
        table = response.xpath("//div[@class='table1']/table")[0]

        for tbody in table.xpath("tbody"):
            loader = ItemLoader(item=RaceResultTimeItem(), selector=tbody)
            loader.add_value("url", response.url + "#result")
            loader.add_xpath("result", "tr/td[1]/text()")
            loader.add_xpath("bracket_number", "tr/td[2]/text()")
            loader.add_xpath("result_time", "tr/td[4]/text()")

            item = loader.load_item()

            self.logger.debug(f"#parse_race_result: result={item}")
            yield item

        # スタート情報
        table = response.xpath("//div[@class='table1']/table")[1]

        for tr in table.xpath("tbody/tr"):
            loader = ItemLoader(item=RaceResultStartTimeItem(), selector=tr)
            loader.add_value("url", response.url + "#start")
            loader.add_xpath("bracket_number", "td/div/span[1]/text()")
            loader.add_xpath("start_time", "translate(normalize-space(td/div/span[3]/span), ' ', '')")

            item = loader.load_item()

            self.logger.debug(f"#parse_race_result: start_time={item}")
            yield item

        # 払い戻し情報
        table = response.xpath("//div[@class='table1']/table")[2]

        bet_type = ""

        for tr in table.xpath("tbody/tr"):
            loader = ItemLoader(item=RaceResultPayoffItem(), selector=tr)
            loader.add_value("url", response.url + "#payoff")

            if len(tr.xpath("td")) == 4:
                bet_type = tr.xpath("td[1]/text()").get()

                loader.add_value("bet_type", bet_type)
                loader.add_xpath("bracket_number", "translate(normalize-space(td[2]), ' ', '')")
                loader.add_xpath("payoff", "string(td[3])")
                loader.add_xpath("favorite", "string(td[4])")
            else:
                loader.add_value("bet_type", bet_type)
                loader.add_xpath("bracket_number", "translate(normalize-space(td[1]), ' ', '')")
                loader.add_xpath("payoff", "string(td[2])")
                loader.add_xpath("favorite", "string(td[3])")

            item = loader.load_item()

            if len(item["bracket_number"][0].strip()) == 0:
                # 空データの場合、読み飛ばす
                continue

            self.logger.debug(f"#parse_race_result: payoff={item}")
            yield item

    def parse_racer_profile(self, response):
        """Parse racer profile page.

        @url https://www.boatrace.jp/owpc/pc/data/racersearch/profile?toban=4463
        @returns items 1 1
        @returns requests 0 0
        @racer_profile_contract
        """
        self.logger.info(f"#parse_racer_profile: start: response={response.url}")

        loader = ItemLoader(item=RacerItem(), selector=response)
        loader.add_value("url", response.url)
        loader.add_xpath("name", "//p[@class='racer1_bodyName']/text()")
        loader.add_xpath("name_kana", "//p[@class='racer1_bodyKana']/text()")
        loader.add_xpath("racer_id", "//dl[@class='list3']/dd[1]/text()")
        loader.add_xpath("birth_day", "//dl[@class='list3']/dd[2]/text()")
        loader.add_xpath("height", "//dl[@class='list3']/dd[3]/text()")
        loader.add_xpath("weight", "//dl[@class='list3']/dd[4]/text()")
        loader.add_xpath("blood_type", "//dl[@class='list3']/dd[5]/text()")
        loader.add_xpath("belong_to", "//dl[@class='list3']/dd[6]/text()")
        loader.add_xpath("birth_place", "//dl[@class='list3']/dd[7]/text()")
        loader.add_xpath("debut_period", "//dl[@class='list3']/dd[8]/text()")
        loader.add_xpath("racer_class", "//dl[@class='list3']/dd[9]/text()")

        item = loader.load_item()

        self.logger.debug(f"#parse_racer_profile: racer={item}")
        yield item
