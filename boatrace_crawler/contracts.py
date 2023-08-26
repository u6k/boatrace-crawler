from urllib.parse import parse_qs, urlparse

from scrapy.contracts import Contract
from scrapy.exceptions import ContractFail
from scrapy.http import Request

from boatrace_crawler.items import OddsItem, RaceIndexItem, RaceProgramBracketItem, RaceProgramBracketResultsItem, RaceProgramItem, RaceResultPayoffItem, RaceResultStartTimeItem, RaceResultTimeItem, RacerItem


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
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/raceindex?jcd=01&hd=20230731"]
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


class RaceProgramContract(Contract):
    name = "race_program_contract"

    def post_process(self, output):
        #
        # Check items
        #
        items = list(filter(lambda o: isinstance(o, RaceProgramItem), output))

        assert len(items) == 1

        i = items[0]
        assert i["course_length"] == ["一般\u3000\u3000\u3000\u3000\u30001800m"]
        assert i["start_time"] == ["17:01"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/racelist?rno=5&jcd=01&hd=20230817"]

        items = list(filter(lambda o: isinstance(o, RaceProgramBracketItem), output))

        assert len(items) == 6

        i = items[0]
        assert i["boat_rate"] == ["42/35.67/52.87"]
        assert i["bracket_number"] == ["１"]
        assert i["motor_rate"] == ["15/42.96/64.44"]
        assert i["racer_data1"] == ["4887/A2"]
        assert i["racer_data2"] == ["群馬/群馬/36歳/52.6kg"]
        assert i["racer_data3"] == ["F1/L0/0.13"]
        assert i["racer_rate_all_place"] == ["5.11/33.62/49.14"]
        assert i["racer_rate_current_place"] == ["5.26/34.02/49.48"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/racelist?rno=5&jcd=01&hd=20230817#bracket"]

        i = items[5]
        assert i["boat_rate"] == ["66/42.00/54.00"]
        assert i["bracket_number"] == ["６"]
        assert i["motor_rate"] == ["37/28.99/44.93"]
        assert i["racer_data1"] == ["5132/B1"]
        assert i["racer_data2"] == ["埼玉/埼玉/24歳/52.5kg"]
        assert i["racer_data3"] == ["F0/L0/0.15"]
        assert i["racer_rate_all_place"] == ["6.01/40.58/59.42"]
        assert i["racer_rate_current_place"] == ["3.88/16.95/28.81"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/racelist?rno=5&jcd=01&hd=20230817#bracket"]

        items = list(filter(lambda o: isinstance(o, RaceProgramBracketResultsItem), output))

        assert len(items) == 42

        i = items[0]
        assert i["approach_course"] == ["4"]
        assert i["bracket_color"] == [" is-boatColor5"]
        assert i["bracket_number"] == ["１"]
        assert i["race_round"] == ["5"]
        assert i["result"] == ["４"]
        assert i["run_number"] == [0]
        assert i["start_timing"] == [".22"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/racelist?rno=5&jcd=01&hd=20230817#bracket_result"]

        i = items[6]
        assert i["approach_course"] == ["4"]
        assert i["bracket_color"] == [" is-boatColor5"]
        assert i["bracket_number"] == ["１"]
        assert i["race_round"] == ["11"]
        assert i["result"] == ["２"]
        assert i["run_number"] == [7]
        assert i["start_timing"] == [".14"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/racelist?rno=5&jcd=01&hd=20230817#bracket_result"]

        i = items[7]
        assert i["approach_course"] == ["4"]
        assert i["bracket_color"] == [" is-boatColor4"]
        assert i["bracket_number"] == ["２"]
        assert i["race_round"] == ["4"]
        assert i["result"] == ["６"]
        assert i["run_number"] == [0]
        assert i["start_timing"] == [".26"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/racelist?rno=5&jcd=01&hd=20230817#bracket_result"]

        i = items[41]
        assert i["approach_course"] == ["2"]
        assert i["bracket_color"] == [" is-boatColor2"]
        assert i["bracket_number"] == ["６"]
        assert i["race_round"] == ["2"]
        assert i["result"] == ["２"]
        assert i["run_number"] == [8]
        assert i["start_timing"] == [".14"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/racelist?rno=5&jcd=01&hd=20230817#bracket_result"]

        #
        # Check requests
        #
        requests = list(filter(lambda o: isinstance(o, Request), output))

        assert requests[0].url == "https://www.boatrace.jp/owpc/pc/race/odds3t?rno=5&jcd=01&hd=20230817"
        assert requests[1].url == "https://www.boatrace.jp/owpc/pc/race/odds3f?rno=5&jcd=01&hd=20230817"
        assert requests[2].url == "https://www.boatrace.jp/owpc/pc/race/odds2tf?rno=5&jcd=01&hd=20230817"
        assert requests[3].url == "https://www.boatrace.jp/owpc/pc/race/oddsk?rno=5&jcd=01&hd=20230817"
        assert requests[4].url == "https://www.boatrace.jp/owpc/pc/race/oddstf?rno=5&jcd=01&hd=20230817"
        assert requests[5].url == "https://www.boatrace.jp/owpc/pc/race/raceresult?rno=5&jcd=01&hd=20230817"
        assert requests[6].url == "https://www.boatrace.jp/owpc/pc/data/racersearch/profile?toban=4887"
        assert requests[7].url == "https://www.boatrace.jp/owpc/pc/data/racersearch/profile?toban=4305"
        assert requests[8].url == "https://www.boatrace.jp/owpc/pc/data/racersearch/profile?toban=5133"
        assert requests[9].url == "https://www.boatrace.jp/owpc/pc/data/racersearch/profile?toban=4916"
        assert requests[10].url == "https://www.boatrace.jp/owpc/pc/data/racersearch/profile?toban=3414"
        assert requests[11].url == "https://www.boatrace.jp/owpc/pc/data/racersearch/profile?toban=5132"


class Odds3tContract(Contract):
    name = "odds_3t_contract"

    def post_process(self, output):
        #
        # Check items
        #
        items = list(filter(lambda o: isinstance(o, OddsItem), output))

        assert len(items) == 120

        i = items[0]
        assert i["bracket_number_1"] == ["1"]
        assert i["bracket_number_2"] == ["2"]
        assert i["bracket_number_3"] == ["3"]
        assert i["odds"] == ["11.2"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/odds3t?rno=5&jcd=01&hd=20230817"]

        i = items[3]
        assert i["bracket_number_1"] == ["1"]
        assert i["bracket_number_2"] == ["2"]
        assert i["bracket_number_3"] == ["6"]
        assert i["odds"] == ["20.4"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/odds3t?rno=5&jcd=01&hd=20230817"]

        i = items[4]
        assert i["bracket_number_1"] == ["1"]
        assert i["bracket_number_2"] == ["3"]
        assert i["bracket_number_3"] == ["2"]
        assert i["odds"] == ["16.8"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/odds3t?rno=5&jcd=01&hd=20230817"]

        i = items[20]
        assert i["bracket_number_1"] == ["2"]
        assert i["bracket_number_2"] == ["1"]
        assert i["bracket_number_3"] == ["3"]
        assert i["odds"] == ["42.3"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/odds3t?rno=5&jcd=01&hd=20230817"]

        i = items[119]
        assert i["bracket_number_1"] == ["6"]
        assert i["bracket_number_2"] == ["5"]
        assert i["bracket_number_3"] == ["4"]
        assert i["odds"] == ["641.9"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/odds3t?rno=5&jcd=01&hd=20230817"]


class Odds3fContract(Contract):
    name = "odds_3f_contract"

    def post_process(self, output):
        #
        # Check items
        #
        items = list(filter(lambda o: isinstance(o, OddsItem), output))

        assert len(items) == 20

        i = items[0]
        assert i["bracket_number_1"] == [1]
        assert i["bracket_number_2"] == [2]
        assert i["bracket_number_3"] == [3]
        assert i["odds"] == ["4.1"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/odds3f?rno=5&jcd=01&hd=20230817"]

        i = items[1]
        assert i["bracket_number_1"] == [1]
        assert i["bracket_number_2"] == [2]
        assert i["bracket_number_3"] == [4]
        assert i["odds"] == ["7.1"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/odds3f?rno=5&jcd=01&hd=20230817"]

        i = items[2]
        assert i["bracket_number_1"] == [1]
        assert i["bracket_number_2"] == [2]
        assert i["bracket_number_3"] == [5]
        assert i["odds"] == ["4.0"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/odds3f?rno=5&jcd=01&hd=20230817"]

        i = items[3]
        assert i["bracket_number_1"] == [1]
        assert i["bracket_number_2"] == [2]
        assert i["bracket_number_3"] == [6]
        assert i["odds"] == ["13.2"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/odds3f?rno=5&jcd=01&hd=20230817"]

        i = items[4]
        assert i["bracket_number_1"] == [1]
        assert i["bracket_number_2"] == [3]
        assert i["bracket_number_3"] == [4]
        assert i["odds"] == ["13.2"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/odds3f?rno=5&jcd=01&hd=20230817"]

        i = items[5]
        assert i["bracket_number_1"] == [1]
        assert i["bracket_number_2"] == [3]
        assert i["bracket_number_3"] == [5]
        assert i["odds"] == ["10.0"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/odds3f?rno=5&jcd=01&hd=20230817"]

        i = items[6]
        assert i["bracket_number_1"] == [1]
        assert i["bracket_number_2"] == [3]
        assert i["bracket_number_3"] == [6]
        assert i["odds"] == ["23.2"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/odds3f?rno=5&jcd=01&hd=20230817"]

        i = items[7]
        assert i["bracket_number_1"] == [1]
        assert i["bracket_number_2"] == [4]
        assert i["bracket_number_3"] == [5]
        assert i["odds"] == ["10.7"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/odds3f?rno=5&jcd=01&hd=20230817"]

        i = items[8]
        assert i["bracket_number_1"] == [1]
        assert i["bracket_number_2"] == [4]
        assert i["bracket_number_3"] == [6]
        assert i["odds"] == ["21.8"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/odds3f?rno=5&jcd=01&hd=20230817"]

        i = items[9]
        assert i["bracket_number_1"] == [1]
        assert i["bracket_number_2"] == [5]
        assert i["bracket_number_3"] == [6]
        assert i["odds"] == ["21.3"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/odds3f?rno=5&jcd=01&hd=20230817"]

        i = items[10]
        assert i["bracket_number_1"] == [2]
        assert i["bracket_number_2"] == [3]
        assert i["bracket_number_3"] == [4]
        assert i["odds"] == ["13.2"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/odds3f?rno=5&jcd=01&hd=20230817"]

        i = items[11]
        assert i["bracket_number_1"] == [2]
        assert i["bracket_number_2"] == [3]
        assert i["bracket_number_3"] == [5]
        assert i["odds"] == ["10.0"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/odds3f?rno=5&jcd=01&hd=20230817"]

        i = items[12]
        assert i["bracket_number_1"] == [2]
        assert i["bracket_number_2"] == [3]
        assert i["bracket_number_3"] == [6]
        assert i["odds"] == ["23.2"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/odds3f?rno=5&jcd=01&hd=20230817"]

        i = items[13]
        assert i["bracket_number_1"] == [2]
        assert i["bracket_number_2"] == [4]
        assert i["bracket_number_3"] == [5]
        assert i["odds"] == ["10.7"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/odds3f?rno=5&jcd=01&hd=20230817"]

        i = items[14]
        assert i["bracket_number_1"] == [2]
        assert i["bracket_number_2"] == [4]
        assert i["bracket_number_3"] == [6]
        assert i["odds"] == ["21.8"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/odds3f?rno=5&jcd=01&hd=20230817"]

        i = items[15]
        assert i["bracket_number_1"] == [2]
        assert i["bracket_number_2"] == [5]
        assert i["bracket_number_3"] == [6]
        assert i["odds"] == ["21.3"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/odds3f?rno=5&jcd=01&hd=20230817"]

        i = items[16]
        assert i["bracket_number_1"] == [3]
        assert i["bracket_number_2"] == [4]
        assert i["bracket_number_3"] == [5]
        assert i["odds"] == ["10.7"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/odds3f?rno=5&jcd=01&hd=20230817"]

        i = items[17]
        assert i["bracket_number_1"] == [3]
        assert i["bracket_number_2"] == [4]
        assert i["bracket_number_3"] == [6]
        assert i["odds"] == ["21.8"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/odds3f?rno=5&jcd=01&hd=20230817"]

        i = items[18]
        assert i["bracket_number_1"] == [3]
        assert i["bracket_number_2"] == [5]
        assert i["bracket_number_3"] == [6]
        assert i["odds"] == ["21.3"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/odds3f?rno=5&jcd=01&hd=20230817"]

        i = items[19]
        assert i["bracket_number_1"] == [4]
        assert i["bracket_number_2"] == [5]
        assert i["bracket_number_3"] == [6]
        assert i["odds"] == ["21.3"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/odds3f?rno=5&jcd=01&hd=20230817"]


class Odds2tfContract(Contract):
    name = "odds_2tf_contract"

    def post_process(self, output):
        #
        # Check items
        #

        # 2連単オッズ
        items = list(filter(lambda o: isinstance(o, OddsItem) and o["url"][0].endswith("#odds2t"), output))

        assert len(items) == 30

        i = items[0]
        assert i["bracket_number_1"] == ["1"]
        assert i["bracket_number_2"] == ["2"]
        assert i["odds"] == ["2.7"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/odds2tf?rno=5&jcd=01&hd=20230817#odds2t"]

        i = items[4]
        assert i["bracket_number_1"] == ["1"]
        assert i["bracket_number_2"] == ["6"]
        assert i["odds"] == ["30.0"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/odds2tf?rno=5&jcd=01&hd=20230817#odds2t"]

        i = items[5]
        assert i["bracket_number_1"] == ["2"]
        assert i["bracket_number_2"] == ["1"]
        assert i["odds"] == ["11.8"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/odds2tf?rno=5&jcd=01&hd=20230817#odds2t"]

        i = items[29]
        assert i["bracket_number_1"] == ["6"]
        assert i["bracket_number_2"] == ["5"]
        assert i["odds"] == ["171.7"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/odds2tf?rno=5&jcd=01&hd=20230817#odds2t"]

        # 2連複オッズ
        items = list(filter(lambda o: isinstance(o, OddsItem) and o["url"][0].endswith("#odds2f"), output))

        assert len(items) == 15

        i = items[0]
        assert i["bracket_number_1"] == ["1"]
        assert i["bracket_number_2"] == ["2"]
        assert i["odds"] == ["2.4"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/odds2tf?rno=5&jcd=01&hd=20230817#odds2f"]

        i = items[4]
        assert i["bracket_number_1"] == ["1"]
        assert i["bracket_number_2"] == ["6"]
        assert i["odds"] == ["19.3"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/odds2tf?rno=5&jcd=01&hd=20230817#odds2f"]

        i = items[5]
        assert i["bracket_number_1"] == ["2"]
        assert i["bracket_number_2"] == ["3"]
        assert i["odds"] == ["36.2"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/odds2tf?rno=5&jcd=01&hd=20230817#odds2f"]

        i = items[14]
        assert i["bracket_number_1"] == ["5"]
        assert i["bracket_number_2"] == ["6"]
        assert i["odds"] == ["61.7"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/odds2tf?rno=5&jcd=01&hd=20230817#odds2f"]


class OddskContract(Contract):
    name = "odds_k_contract"

    def post_process(self, output):
        #
        # Check items
        #
        items = list(filter(lambda o: isinstance(o, OddsItem), output))

        assert len(items) == 15

        i = items[0]
        assert i["bracket_number_1"] == ["1"]
        assert i["bracket_number_2"] == ["2"]
        assert i["odds"] == ["1.0-1.1"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/oddsk?rno=5&jcd=01&hd=20230817"]

        i = items[4]
        assert i["bracket_number_1"] == ["1"]
        assert i["bracket_number_2"] == ["6"]
        assert i["odds"] == ["4.7-7.0"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/oddsk?rno=5&jcd=01&hd=20230817"]

        i = items[5]
        assert i["bracket_number_1"] == ["2"]
        assert i["bracket_number_2"] == ["3"]
        assert i["odds"] == ["3.9-6.7"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/oddsk?rno=5&jcd=01&hd=20230817"]

        i = items[14]
        assert i["bracket_number_1"] == ["5"]
        assert i["bracket_number_2"] == ["6"]
        assert i["odds"] == ["9.2-10.1"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/oddsk?rno=5&jcd=01&hd=20230817"]


class OddstfContract(Contract):
    name = "odds_tf_contract"

    def post_process(self, output):
        #
        # Check items
        #
        items = list(filter(lambda o: isinstance(o, OddsItem), output))

        assert len(items) == 12

        i = items[0]
        assert i["bracket_number_1"] == ["1"]
        assert i["odds"] == ["1.2"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/oddstf?rno=5&jcd=01&hd=20230817#oddst"]

        i = items[5]
        assert i["bracket_number_1"] == ["6"]
        assert i["odds"] == ["10.9"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/oddstf?rno=5&jcd=01&hd=20230817#oddst"]

        i = items[6]
        assert i["bracket_number_1"] == ["1"]
        assert i["odds"] == ["1.0-1.4"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/oddstf?rno=5&jcd=01&hd=20230817#oddsf"]

        i = items[11]
        assert i["bracket_number_1"] == ["6"]
        assert i["odds"] == ["4.3-6.4"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/oddstf?rno=5&jcd=01&hd=20230817#oddsf"]


class RaceResultContract(Contract):
    name = "race_result_contract"

    def post_process(self, output):
        #
        # Check items
        #

        # 着順
        items = list(filter(lambda o: isinstance(o, RaceResultTimeItem), output))

        assert len(items) == 6

        i = items[0]
        assert i["bracket_number"] == ["1"]
        assert i["result"] == ["１"]
        assert i["result_time"] == ["1'51\"7"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/raceresult?rno=5&jcd=01&hd=20230817#result"]

        i = items[5]
        assert i["bracket_number"] == ["3"]
        assert i["result"] == ["６"]
        assert i["result_time"] == ["1'59\"1"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/raceresult?rno=5&jcd=01&hd=20230817#result"]

        # スタート情報
        items = list(filter(lambda o: isinstance(o, RaceResultStartTimeItem), output))

        assert len(items) == 6

        i = items[0]
        assert i["bracket_number"] == ["1"]
        assert i["start_time"] == [".14\xa0\xa0\xa0逃げ"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/raceresult?rno=5&jcd=01&hd=20230817#start"]

        i = items[5]
        assert i["bracket_number"] == ["6"]
        assert i["start_time"] == [".11\xa0\xa0\xa0\xa0"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/raceresult?rno=5&jcd=01&hd=20230817#start"]

        # オッズ情報
        items = list(filter(lambda o: isinstance(o, RaceResultPayoffItem), output))

        assert len(items) == 10

        i = items[0]
        assert i["bet_type"] == ["3連単"]
        assert i["bracket_number"] == ["1-4-2"]
        assert i["favorite"] == ["8"]
        assert i["payoff"] == ["¥2,550"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/raceresult?rno=5&jcd=01&hd=20230817#payoff"]

        i = items[1]
        assert i["bet_type"] == ["3連複"]
        assert i["bracket_number"] == ["1=2=4"]
        assert i["favorite"] == ["3"]
        assert i["payoff"] == ["¥710"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/raceresult?rno=5&jcd=01&hd=20230817#payoff"]

        i = items[2]
        assert i["bet_type"] == ["2連単"]
        assert i["bracket_number"] == ["1-4"]
        assert i["favorite"] == ["5"]
        assert i["payoff"] == ["¥1,250"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/raceresult?rno=5&jcd=01&hd=20230817#payoff"]

        i = items[3]
        assert i["bet_type"] == ["2連複"]
        assert i["bracket_number"] == ["1=4"]
        assert i["favorite"] == ["2"]
        assert i["payoff"] == ["¥420"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/raceresult?rno=5&jcd=01&hd=20230817#payoff"]

        i = items[4]
        assert i["bet_type"] == ["拡連複"]
        assert i["bracket_number"] == ["1=4"]
        assert i["favorite"] == ["5"]
        assert i["payoff"] == ["¥310"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/raceresult?rno=5&jcd=01&hd=20230817#payoff"]

        i = items[5]
        assert i["bet_type"] == ["拡連複"]
        assert i["bracket_number"] == ["1=2"]
        assert i["favorite"] == ["1"]
        assert i["payoff"] == ["¥110"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/raceresult?rno=5&jcd=01&hd=20230817#payoff"]

        i = items[6]
        assert i["bet_type"] == ["拡連複"]
        assert i["bracket_number"] == ["2=4"]
        assert i["favorite"] == ["7"]
        assert i["payoff"] == ["¥430"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/raceresult?rno=5&jcd=01&hd=20230817#payoff"]

        i = items[7]
        assert i["bet_type"] == ["単勝"]
        assert i["bracket_number"] == ["1"]
        assert i["favorite"] == ["\xa0"]
        assert i["payoff"] == ["¥120"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/raceresult?rno=5&jcd=01&hd=20230817#payoff"]

        i = items[8]
        assert i["bet_type"] == ["複勝"]
        assert i["bracket_number"] == ["1"]
        assert i["favorite"] == ["\xa0"]
        assert i["payoff"] == ["¥140"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/raceresult?rno=5&jcd=01&hd=20230817#payoff"]

        i = items[9]
        assert i["bet_type"] == ["複勝"]
        assert i["bracket_number"] == ["4"]
        assert i["favorite"] == ["\xa0"]
        assert i["payoff"] == ["¥410"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/race/raceresult?rno=5&jcd=01&hd=20230817#payoff"]


class RacerProfileContract(Contract):
    name = "racer_profile_contract"

    def post_process(self, output):
        #
        # Check items
        #
        items = list(filter(lambda o: isinstance(o, RacerItem), output))

        assert len(items) == 1

        i = items[0]
        assert i["belong_to"] == ["福岡"]
        assert i["birth_day"] == ["1986/05/26"]
        assert i["birth_place"] == ["福岡県"]
        assert i["blood_type"] == ["B型"]
        assert i["debut_period"] == ["101期"]
        assert i["height"] == ["166cm"]
        assert i["name"] == ["三苫\u3000\u3000晃幸"]
        assert i["name_kana"] == ["ミトマ\u3000テルユキ"]
        assert i["racer_class"] == ["A2級"]
        assert i["racer_id"] == ["4463"]
        assert i["url"] == ["https://www.boatrace.jp/owpc/pc/data/racersearch/profile?toban=4463"]
        assert i["weight"] == ["55kg"]
