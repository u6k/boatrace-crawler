from urllib.parse import parse_qs, urlparse

from scrapy.contracts import Contract
from scrapy.exceptions import ContractFail
from scrapy.http import Request

from boatrace_crawler.items import RaceIndexItem


class CalendarContract(Contract):
    name = "calendar_contract"

    def post_process(self, output):
        # Check requests
        requests = list(filter(lambda o: isinstance(o, Request), output))

        for r in requests:
            url = urlparse(r.url)
            qs = parse_qs(url.query)

            if url.path == "/owpc/pc/race/raceindex" and "jcd" in qs and "hd" in qs:
                continue

            raise ContractFail(f"Unknown request: url={r.url}")


class RaceIndexContract(Contract):
    name = "race_index_contract"

    def post_process(self, output):
        #
        # Check items
        #
        items = list(filter(lambda o: isinstance(o, RaceIndexItem), output))

        assert len(items) == 1

        i = items[0]
        assert i["place_id"] == ["01"]
        assert i["place_name"] == ["桐生"]
        assert i["race_grade"] == ["heading2_title is-G3b "]
        assert i["race_name"] == ["マスターズＬ第４戦　ドラキリュウナイトカップ"]
        assert i["race_index_urls"] == ["https://www.boatrace.jp/owpc/pc/race/raceindex?jcd=01&hd=20230729", "https://www.boatrace.jp/owpc/pc/race/raceindex?jcd=01&hd=20230730", "https://www.boatrace.jp/owpc/pc/race/raceindex?jcd=01&hd=20230801", "https://www.boatrace.jp/owpc/pc/race/raceindex?jcd=01&hd=20230802", "https://www.boatrace.jp/owpc/pc/race/raceindex?jcd=01&hd=20230803", "https://www.boatrace.jp/owpc/pc/race/raceindex?jcd=01&hd=20230731"]

        #
        # Check requests
        #
        requests = list(filter(lambda o: isinstance(o, Request), output))

        for r in requests:
            url = urlparse(r.url)
            qs = parse_qs(url.query)

            if url.path == "/owpc/pc/race/raceindex" and "jcd" in qs and "hd" in qs:
                continue

            if url.path == "/owpc/pc/race/racelist" and "rno" in qs and "jcd" in qs and "hd" in qs:
                continue

            raise ContractFail(f"Unknown request: url={r.url}")
