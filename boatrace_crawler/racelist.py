import io
import json
import logging
import logging.config
import os
import re
import subprocess
import warnings
from datetime import datetime, timedelta

import pandas as pd

#
# ログ設定
#

logging.config.fileConfig("./logging.conf")


def get_logger(task_name):
    return logging.getLogger(f"boatrace_crawler.{task_name}")


warnings.simplefilter("ignore")


#
# S3操作
#


def get_feed(s3_client, feed_url):
    key_re = re.fullmatch(r"^s3://(\w+)/(.*)$", feed_url)
    s3_key = key_re.group(2)

    with io.BytesIO(s3_client.get_bytes(s3_key)) as b:
        json_data = json.load(b)

    return json_data


def get_racelist(s3_client, racelist_folder, target_date):
    key = f"{racelist_folder}/{target_date.strftime('%Y%m%d')}/df_racelist.joblib"

    df = s3_client.get(key)

    return df


def put_racelist(s3_client, df_arg, racelist_folder, target_date):
    key_base = f"{racelist_folder}/{target_date.strftime('%Y%m%d')}/df_racelist"

    with io.BytesIO() as b:
        df_arg.to_csv(b)

        s3_client.put_bytes(key_base + ".csv", b.getvalue())

    s3_client.put(key_base + ".joblib", df_arg)

    return key_base + ".joblib"


#
# レースデータ
#


def extract_racelist(df_race_info, target_date):
    start_datetime = target_date
    end_datetime = start_datetime + timedelta(days=1)

    # 当日レースを抽出する
    df_race_info = df_race_info.query(f"'{start_datetime}'<=start_datetime<'{end_datetime}'").sort_values("start_datetime").reset_index(drop=True)

    # n分刻みのレース一覧を生成する
    dict_racelist = {
        "race_id": [],
        "diff_minutes": [],
        "place_id": [],
        "race_round": [],
        "start_datetime": [],
        "crawl_start_datetime": [],
        "crawl_datetime": [],
        "key": [],
    }

    for _, row in df_race_info.iterrows():
        for diff_minutes in [30, 20, 15, 10, 5, 2]:
            dict_racelist["race_id"].append(row["race_id"])
            dict_racelist["place_id"].append(row["place_id"])
            dict_racelist["race_round"].append(row["race_round"])
            dict_racelist["start_datetime"].append(row["start_datetime"])

            dict_racelist["diff_minutes"].append(diff_minutes)
            dict_racelist["crawl_start_datetime"].append(row["start_datetime"] - timedelta(minutes=diff_minutes))
            dict_racelist["crawl_datetime"].append(None)
            dict_racelist["key"].append(f"{row['race_id']}_before_{diff_minutes}minutes")

    df_racelist = pd.DataFrame(dict_racelist) \
        .sort_values(["start_datetime", "crawl_start_datetime"]) \
        .astype({
            "race_id": "str",
            "diff_minutes": "int",
            "place_id": "str",
            "race_round": "int",
            "start_datetime": "datetime64[ns]",
            "crawl_start_datetime": "datetime64[ns]",
            "crawl_datetime": "datetime64[ns]",
        }) \
        .set_index("key")

    return df_racelist


def extract_not_crawl_racelist(df_arg_racelist, arg_crawl_queue, now_datetime):
    """
    クロール開始時刻に達した、かつ、クロールキューに存在しないレースを抽出する。
    """

    # クロールが終了していない、かつ、クロール開始時刻に達したレースを抽出する。
    df_tmp = df_arg_racelist.query(f"crawl_datetime.isnull() and crawl_start_datetime<='{now_datetime}'")

    # クロールキューに存在するレースをレース一覧から削除する。
    df_tmp = df_tmp.drop(list(arg_crawl_queue.keys()))

    return df_tmp


def crawl_race_subprocess(race_item, file_suffix):
    L = get_logger("crawl_race")

    L.debug(f"race_item={race_item}")
    L.debug(f"file_suffix={file_suffix}")

    # パラメーターを構築する
    start_url = f"https://www.boatrace.jp/owpc/pc/race/racelist?rno={race_item['race_round']}&jcd={race_item['place_id']}&hd={race_item['start_datetime'].strftime('%Y%m%d')}"

    env = os.environ.copy()
    env["AWS_S3_FEED_URL"] = f"s3://{env['AWS_S3_CACHE_BUCKET']}/{env['AWS_S3_RACELIST_FOLDER']}/{race_item['start_datetime'].strftime('%Y%m%d')}/race_{race_item['race_id']}_{file_suffix}.json"
    env["RECACHE_RACE"] = "True"
    env["RECACHE_DATA"] = "False"
    del env["CRAWL_HTTP_PROXY"]

    L.debug(f"start_url={start_url}")
    L.debug(f"env={env}")

    # クロールプロセスを起動する
    proc = subprocess.Popen(["scrapy", "crawl", "boatrace_spider", "-a", f"start_url={start_url}"], env=env)

    return proc


#
# フィードjson
#


def parse_race_index(json_data):
    race_index_url_pattern = re.compile(r"https:\/\/www\.boatrace\.jp\/owpc\/pc\/race\/raceindex\?jcd=([0-9]{2})&hd=([0-9]{8})")

    i = {
        "place_id": json_data["place_id"][0],  # "place_id": ["01"],
        "place_name": json_data["place_name"][0],  # "place_name": ["桐生"]
        "race_name": json_data["race_name"][0],  # "race_name": ["ヴィーナスシリーズ第７戦　第１６回マクール杯"]
    }

    # レース節ID
    race_index_ids = []
    for u in json_data["race_index_urls"]:  # "race_index_urls": ["https://www.boatrace.jp/owpc/pc/race/raceindex?jcd=01&hd=20230705", "https://www.boatrace.jp/owpc/pc/race/raceindex?jcd=01&hd=20230706", "https://www.boatrace.jp/owpc/pc/race/raceindex?jcd=01&hd=20230707", "https://www.boatrace.jp/owpc/pc/race/raceindex?jcd=01&hd=20230708", "https://www.boatrace.jp/owpc/pc/race/raceindex?jcd=01&hd=20230709", "https://www.boatrace.jp/owpc/pc/race/raceindex?jcd=01&hd=20230710"]}
        race_index_url_re = race_index_url_pattern.search(u)
        if race_index_url_re:
            race_index_ids.append(race_index_url_re.group(2) + "_" + race_index_url_re.group(1))
        else:
            raise Exception(f"Unknown ace_index_urls: {json_data}")

    race_index_ids = sorted(race_index_ids)
    i["race_index_id"] = race_index_ids[0]

    # グレード
    if "is-ippan" in json_data["race_grade"][0]:  # "race_grade": ["heading2_title is-ippan "]
        i["race_grade_type"] = 0
    elif "is-G3" in json_data["race_grade"][0]:
        i["race_grade_type"] = 1
    elif "is-G2" in json_data["race_grade"][0]:
        i["race_grade_type"] = 2
    elif "is-G1" in json_data["race_grade"][0]:
        i["race_grade_type"] = 3
    elif "is-SG" in json_data["race_grade"][0]:
        i["race_grade_type"] = 4
    else:
        raise Exception(f"Unknown race_grade: {json_data}")

    # 親レース節IDとの紐づけ
    join_i = []
    for race_index_id in race_index_ids:
        join_i.append(
            {
                "race_index_id": i["race_index_id"],
                "child_id": race_index_id,
            }
        )

    return i, join_i


def parse_race_bracket(json_data):
    race_url_pattern = re.compile(r"https:\/\/www\.boatrace\.jp\/owpc\/pc\/race\/racelist\?rno=([0-9]+)&jcd=([0-9]{2})&hd=([0-9]{8})")

    i = {
        "bracket_number": int(json_data["bracket_number"][0]),  # "bracket_number": ["２"]
    }

    race_url_re = race_url_pattern.search(json_data["url"][0])  # "url": ["https://www.boatrace.jp/owpc/pc/race/racelist?rno=12&jcd=01&hd=20230710#bracket"]
    if race_url_re:
        i["race_id"] = race_url_re.group(3) + "_" + race_url_re.group(2) + "_" + race_url_re.group(1)
    else:
        raise Exception(f"Unknown race_url: {json_data}")

    racer_data1 = json_data["racer_data1"][0].split("/")  # "racer_data1": ["4530/B2"]
    i["racer_id"] = racer_data1[0]

    if racer_data1[1] == "A1":
        i["racer_class_type"] = 1
    elif racer_data1[1] == "A2":
        i["racer_class_type"] = 2
    elif racer_data1[1] == "B1":
        i["racer_class_type"] = 3
    elif racer_data1[1] == "B2":
        i["racer_class_type"] = 4
    else:
        raise Exception(f"Unknown racer_class: {json_data}")

    racer_data2 = json_data["racer_data2"][0].split("/")  # "racer_data2": ["福岡/福岡/34歳/44.5kg"]
    i["belong_to"] = racer_data2[0]
    i["birth_place"] = racer_data2[1]
    i["age"] = int(racer_data2[2].replace("歳", ""))
    if racer_data2[3] == "-":
        i["weight"] = None
    else:
        i["weight"] = float(racer_data2[3].replace("kg", ""))

    racer_data3 = json_data["racer_data3"][0].split("/")  # "racer_data3": ["F0/L0/0.16"]
    i["flying_start_count"] = int(racer_data3[0].replace("F", ""))
    i["late_start_count"] = int(racer_data3[1].replace("L", ""))
    if racer_data3[2] == "-":
        i["average_start_timing"] = None
    else:
        i["average_start_timing"] = float(racer_data3[2])

    racer_rate_all_place = json_data["racer_rate_all_place"][0].split("/")  # "racer_rate_all_place": ["7.06/53.62/75.36"]
    i["first_place_rate_all_place"] = float(racer_rate_all_place[0])
    i["second_place_rate_all_place"] = float(racer_rate_all_place[1])
    i["third_place_rate_all_place"] = float(racer_rate_all_place[2])

    racer_rate_current_place = json_data["racer_rate_current_place"][0].split("/")  # "racer_rate_current_place": ["6.40/50.00/70.00"]
    i["first_place_rate_current_place"] = float(racer_rate_current_place[0])
    i["second_place_rate_current_place"] = float(racer_rate_current_place[1])
    i["third_place_rate_current_place"] = float(racer_rate_current_place[2])

    motor_rate = json_data["motor_rate"][0].split("/")  # "motor_rate": ["20/35.35/49.49"]
    i["motor_id"] = int(motor_rate[0])
    i["second_place_rate_motor"] = float(motor_rate[1])
    i["third_place_rate_motor"] = float(motor_rate[2])

    boat_rate = json_data["boat_rate"][0].split("/")  # "boat_rate": ["18/32.56/52.71"]
    i["boat_id"] = int(boat_rate[0])
    i["second_place_rate_boat"] = float(boat_rate[1])
    i["third_place_rate_boat"] = float(boat_rate[2])

    return i


def parse_race_bracket_result(json_data):
    boat_color_pattern = re.compile(r"is-boatColor([0-9])")
    race_url_pattern = re.compile(r"https:\/\/www\.boatrace\.jp\/owpc\/pc\/race\/racelist\?rno=([0-9]+)&jcd=([0-9]{2})&hd=([0-9]{8})")

    i = {
        "bracket_number": int(json_data["bracket_number"][0]),  # "bracket_number": ["１"]
        "run_number": int(json_data["run_number"][0]),  # "run_number": [0]
        "race_round": int(json_data["race_round"][0]),  # "race_round": ["8"]
        "start_timing": float("0" + json_data["start_timing"][0]),  # "start_timing": [".25"]
    }

    if json_data["result"][0] == "転":  # "result": ["１"]
        i["result"] = -1
    elif json_data["result"][0] == "落":
        i["result"] = -2
    elif json_data["result"][0] == "エ":
        i["result"] = -3
    elif json_data["result"][0] == "妨":
        i["result"] = -4
    elif json_data["result"][0] == "Ｆ":
        i["result"] = -5
    elif json_data["result"][0] == "Ｌ":
        i["result"] = -6
    elif json_data["result"][0] == "不":
        i["result"] = -7
    elif json_data["result"][0] == "欠":
        i["result"] = -8
    elif json_data["result"][0] == "沈":
        i["result"] = -9
    elif json_data["result"][0] == "＿":
        i["result"] = -10
    elif json_data["result"][0] == "失":
        i["result"] = -11
    else:
        i["result"] = int(json_data["result"][0])

    if json_data["approach_course"][0] == "\xa0":  # "approach_course": ["4"]
        i["approach_course"] = None
    else:
        i["approach_course"] = int(json_data["approach_course"][0])

    race_url_re = race_url_pattern.search(json_data["url"][0])  # "url": ["https://www.boatrace.jp/owpc/pc/race/racelist?rno=12&jcd=01&hd=20230710#bracket_result"]
    if race_url_re:
        i["race_id"] = race_url_re.group(3) + "_" + race_url_re.group(2) + "_" + race_url_re.group(1)
    else:
        raise Exception(f"Unknown race_url: {json_data}")

    boat_color_re = boat_color_pattern.search(json_data["bracket_color"][0])  # "bracket_color": [" is-boatColor5"]
    if boat_color_re:
        i["bracket_number_run"] = int(boat_color_re.group(1))
    else:
        raise Exception(f"Unknown boat_color: {json_data}")

    return i


def parse_race_info(json_data):
    course_length_pattern = re.compile(r"(.+?)([0-9]+)m")
    race_url_pattern = re.compile(r"https:\/\/www\.boatrace\.jp\/owpc\/pc\/race\/racelist\?rno=([0-9]+)&jcd=([0-9]{2})&hd=([0-9]{8})")

    i = {}

    race_url_re = race_url_pattern.search(json_data["url"][0])  # "url": ["https://www.boatrace.jp/owpc/pc/race/racelist?rno=12&jcd=24&hd=20230731"]
    if race_url_re:
        i["race_id"] = race_url_re.group(3) + "_" + race_url_re.group(2) + "_" + race_url_re.group(1)
    else:
        raise Exception(f"Unknown race_url: {json_data}")

    i["race_round"] = int(race_url_re.group(1))
    i["place_id"] = race_url_re.group(2)

    i["start_datetime"] = datetime.strptime(race_url_re.group(3) + " " + json_data["start_time"][0], "%Y%m%d %H:%M")  # "start_time": ["20:38"]

    course_length_re = course_length_pattern.search(json_data["course_length"][0])  # "course_length": ["優勝戦　　　　1800m"]
    if course_length_re:
        i["race_subname"] = course_length_re.group(1).strip()
        i["course_length"] = int(course_length_re.group(2))
    else:
        raise Exception(f"Unknown course_length: {json_data}")

    return i


def parse_race_result(json_data):
    race_result_url_pattern = re.compile(r"https:\/\/www\.boatrace\.jp\/owpc\/pc\/race\/raceresult\?rno=([0-9]+)&jcd=([0-9]{2})&hd=([0-9]{8})")
    result_time_pattern = re.compile(r"([0-9]+)\'([0-9]+)\"([0-9]+)")

    i = {
        "bracket_number": int(json_data["bracket_number"][0]),  # "bracket_number": ["3"]
    }

    if json_data["result"][0] == "転":  # "result": ["２"]
        i["result"] = -1
    elif json_data["result"][0] == "落":
        i["result"] = -2
    elif json_data["result"][0] == "エ":
        i["result"] = -3
    elif json_data["result"][0] == "妨":
        i["result"] = -4
    elif json_data["result"][0] == "Ｆ":
        i["result"] = -5
    elif json_data["result"][0] == "Ｌ":
        i["result"] = -6
    elif json_data["result"][0] == "不":
        i["result"] = -7
    elif json_data["result"][0] == "欠":
        i["result"] = -8
    elif json_data["result"][0] == "沈":
        i["result"] = -9
    elif json_data["result"][0] == "＿":
        i["result"] = -10
    elif json_data["result"][0] == "失":
        i["result"] = -11
    else:
        i["result"] = int(json_data["result"][0])

    race_result_url_re = race_result_url_pattern.search(json_data["url"][0])  # "url": ["https://www.boatrace.jp/owpc/pc/race/raceresult?rno=12&jcd=24&hd=20230731#result"]
    if race_result_url_re:
        i["race_id"] = race_result_url_re.group(3) + "_" + race_result_url_re.group(2) + "_" + race_result_url_re.group(1)
    else:
        raise Exception(f"Unknown race_result_url: {json_data}")

    result_time_re = result_time_pattern.search(json_data["result_time"][0])  # "result_time": ["1'51\"0"]
    if result_time_re:
        i["result_time"] = int(result_time_re.group(1)) * 60.0 + int(result_time_re.group(2)) + int(result_time_re.group(3)) / 10.0
    elif len(json_data["result_time"][0].strip()) == 0:
        i["result_time"] = None
    else:
        raise Exception(f"Unknown result_time: {json_data}")

    return i


def parse_race_result_start(json_data):
    start_time_pattern = re.compile(r"(\.[0-9]{2})(.*)")
    race_result_url_pattern = re.compile(r"https:\/\/www\.boatrace\.jp\/owpc\/pc\/race\/raceresult\?rno=([0-9]+)&jcd=([0-9]{2})&hd=([0-9]{8})")

    i = {
        "bracket_number": int(json_data["bracket_number"][0]),  # "bracket_number": ["1"]
    }

    race_result_url_re = race_result_url_pattern.search(json_data["url"][0])  # "url": ["https://www.boatrace.jp/owpc/pc/race/raceresult?rno=12&jcd=24&hd=20230731#start"]
    if race_result_url_re:
        i["race_id"] = race_result_url_re.group(3) + "_" + race_result_url_re.group(2) + "_" + race_result_url_re.group(1)
    else:
        raise Exception(f"Unknown race_result_url: {json_data}")

    start_time_re = start_time_pattern.search(json_data["start_time"][0])  # "start_time": [".12   まくり"]
    if start_time_re:
        if start_time_re.lastindex == 2:
            i["result_start_time"] = float("0" + start_time_re.group(1))
            i["kimarite"] = start_time_re.group(2).strip()
            if len(i["kimarite"]) == 0:
                i["kimarite"] = None
        elif start_time_re.lastindex == 1:
            i["result_start_time"] = float("0" + start_time_re.group(1))
            i["kimarite"] = None
        else:
            raise Exception(f"Unknown start_time: {json_data}")
    elif json_data["start_time"][0].strip() == "L":
        i["result_start_time"] = None
        i["kimarite"] = None
    else:
        raise Exception(f"Unknown start_time: {json_data}")

    return i


def parse_race_payoff(json_data):
    payoff_bracket_number_3 = re.compile(r"([0-9])=([0-9])")
    payoff_bracket_number_4 = re.compile(r"([0-9])-([0-9])")
    payoff_bracket_number_6 = re.compile(r"([0-9])-([0-9])-([0-9])")
    payoff_bracket_number_7 = re.compile(r"([0-9])=([0-9])=([0-9])")
    race_result_url_pattern = re.compile(r"https:\/\/www\.boatrace\.jp\/owpc\/pc\/race\/raceresult\?rno=([0-9]+)&jcd=([0-9]{2})&hd=([0-9]{8})")

    i = {}

    race_result_url_re = race_result_url_pattern.search(json_data["url"][0])  # "url": ["https://www.boatrace.jp/owpc/pc/race/raceresult?rno=12&jcd=24&hd=20230731#payoff"]
    if race_result_url_re:
        i["race_id"] = race_result_url_re.group(3) + "_" + race_result_url_re.group(2) + "_" + race_result_url_re.group(1)
    else:
        raise Exception(f"Unknown race_result_url: {json_data}")

    if json_data["bet_type"][0] == "単勝":  # "bet_type": ["単勝"]
        i["bet_type"] = 1
    elif json_data["bet_type"][0] == "複勝":
        i["bet_type"] = 2
    elif json_data["bet_type"][0] == "拡連複":
        i["bet_type"] = 3
    elif json_data["bet_type"][0] == "2連単":
        i["bet_type"] = 4
    elif json_data["bet_type"][0] == "2連複":
        i["bet_type"] = 5
    elif json_data["bet_type"][0] == "3連単":
        i["bet_type"] = 6
    elif json_data["bet_type"][0] == "3連複":
        i["bet_type"] = 7
    else:
        raise Exception(f"Unknown bet_type: {json_data}")

    if json_data["bracket_number"][0] == "不成立":
        i["bracket_number_1"] = None

    elif json_data["bracket_number"][0] == "特払":
        i["bracket_number_1"] = None

    else:
        if i["bet_type"] == 1:
            i["bracket_number_1"] = int(json_data["bracket_number"][0])  # "bracket_number": ["2"]

        elif i["bet_type"] == 2:
            i["bracket_number_1"] = int(json_data["bracket_number"][0])  # "bracket_number": ["2"]

        elif i["bet_type"] == 3:
            bracket_number_re = payoff_bracket_number_3.search(json_data["bracket_number"][0])  # "bracket_number": ["3=4"]
            if bracket_number_re:
                i["bracket_number_1"] = int(bracket_number_re.group(1))
                i["bracket_number_2"] = int(bracket_number_re.group(2))
            else:
                raise Exception(f"Unknown bracket_number: {json_data}")

        elif i["bet_type"] == 4:
            bracket_number_re = payoff_bracket_number_4.search(json_data["bracket_number"][0])  # "bracket_number": ["2-3"]
            if bracket_number_re:
                i["bracket_number_1"] = int(bracket_number_re.group(1))
                i["bracket_number_2"] = int(bracket_number_re.group(2))
            else:
                raise Exception(f"Unknown bracket_number: {json_data}")

        elif i["bet_type"] == 5:
            bracket_number_re = payoff_bracket_number_3.search(json_data["bracket_number"][0])  # "bracket_number": ["2=3"]
            if bracket_number_re:
                i["bracket_number_1"] = int(bracket_number_re.group(1))
                i["bracket_number_2"] = int(bracket_number_re.group(2))
            else:
                raise Exception(f"Unknown bracket_number: {json_data}")

        elif i["bet_type"] == 6:
            bracket_number_re = payoff_bracket_number_6.search(json_data["bracket_number"][0])  # "bracket_number": ["2-3-4"]
            if bracket_number_re:
                i["bracket_number_1"] = int(bracket_number_re.group(1))
                i["bracket_number_2"] = int(bracket_number_re.group(2))
                i["bracket_number_3"] = int(bracket_number_re.group(3))
            else:
                raise Exception(f"Unknown bracket_number: {json_data}")

        elif i["bet_type"] == 7:
            bracket_number_re = payoff_bracket_number_7.search(json_data["bracket_number"][0])  # "bracket_number": ["2=3=4"]
            if bracket_number_re:
                i["bracket_number_1"] = int(bracket_number_re.group(1))
                i["bracket_number_2"] = int(bracket_number_re.group(2))
                i["bracket_number_3"] = int(bracket_number_re.group(3))
            else:
                raise Exception(f"Unknown bracket_number: {json_data}")

        else:
            raise Exception(f"Unknown bet_type: {json_data}")

    if len(json_data["favorite"][0].strip()) == 0:  # "favorite": ["1"]
        i["favorite"] = None
    else:
        i["favorite"] = int(json_data["favorite"][0])

    if json_data["payoff"][0] == "\xa0":
        i["payoff"] = None
    else:
        i["payoff"] = int(json_data["payoff"][0].replace("¥", "").replace(",", "")) / 100.0  # "payoff": ["¥1,450"]

    return i


def parse_race_odds(json_data):
    odds_url_pattern = re.compile(r"https:\/\/www\.boatrace\.jp\/owpc\/pc\/race\/(oddstf|oddsk|odds2tf|odds3t|odds3f)\?rno=([0-9]+)&jcd=([0-9]{2})&hd=([0-9]{8})(#oddst|#oddsf|#odds2t|#odds2f)?")
    odds_pattern = re.compile(r"([\.0-9]+)-([\.0-9]+)")

    if "odds" not in json_data:
        # レースが中止になった場合
        return None

    i = {}

    odds_url_re = odds_url_pattern.search(json_data["url"][0])  # "url": ["https://www.boatrace.jp/owpc/pc/race/oddsk?rno=12&jcd=24&hd=20230731"]

    if odds_url_re:
        i["race_id"] = odds_url_re.group(4) + "_" + odds_url_re.group(3) + "_" + odds_url_re.group(2)

        if odds_url_re.group(1) == "oddstf" and odds_url_re.group(5) == "#oddst":
            i["bet_type"] = 1  # 単勝
        elif odds_url_re.group(1) == "oddstf" and odds_url_re.group(5) == "#oddsf":
            i["bet_type"] = 2  # 複勝
        elif odds_url_re.group(1) == "oddsk":
            i["bet_type"] = 3  # 拡張複
        elif odds_url_re.group(1) == "odds2tf" and odds_url_re.group(5) == "#odds2t":
            i["bet_type"] = 4  # 2連単
        elif odds_url_re.group(1) == "odds2tf" and odds_url_re.group(5) == "#odds2f":
            i["bet_type"] = 5  # 2連複
        elif odds_url_re.group(1) == "odds3t":
            i["bet_type"] = 6  # 3連単
        elif odds_url_re.group(1) == "odds3f":
            i["bet_type"] = 7  # 3連複
        else:
            raise Exception(f"Unknown odds_url: {json_data}")
    else:
        raise Exception(f"Unknown odds_url: {json_data}")

    if i["bet_type"] == 1 or i["bet_type"] == 2:
        i["bracket_number_1"] = int(json_data["bracket_number_1"][0])  # "bracket_number_1": ["1"]
    elif i["bet_type"] == 3 or i["bet_type"] == 4 or i["bet_type"] == 5:
        i["bracket_number_1"] = int(json_data["bracket_number_1"][0])
        i["bracket_number_2"] = int(json_data["bracket_number_2"][0])
    else:
        i["bracket_number_1"] = int(json_data["bracket_number_1"][0])
        i["bracket_number_2"] = int(json_data["bracket_number_2"][0])
        i["bracket_number_3"] = int(json_data["bracket_number_3"][0])

    if json_data["odds"][0] == "欠場":
        i["odds_1"] = None
    elif i["bet_type"] == 1 or i["bet_type"] == 4 or i["bet_type"] == 5 or i["bet_type"] == 6 or i["bet_type"] == 7:
        i["odds_1"] = float(json_data["odds"][0])
    else:
        odds_re = odds_pattern.search(json_data["odds"][0])  # "odds": ["2.6-3.4"]
        if odds_re:
            i["odds_1"] = float(odds_re.group(1))
            i["odds_2"] = float(odds_re.group(2))
        else:
            return None
            # TODO: バグ修正後に戻す raise Exception(f"Unknown odds: {json_data}")

    return i


def parse_racer_profile(json_data):
    racer_id_pattern = re.compile(r"([0-9]{4})")

    if "racer_id" not in json_data:
        # データが存在しない場合
        return None

    i = {
        "name": json_data["name"][0],  # "name": ["黒澤　めぐみ"]
        "name_kana": json_data["name_kana"][0],  # "name_kana": ["クロサワ　メグミ"]
        "birth_day": datetime.strptime(json_data["birth_day"][0], "%Y/%m/%d"),  # "birth_day": ["1989/11/13"]
        "height": int(json_data["height"][0].replace("cm", "")),  # "height": ["163cm"]
        "weight": int(json_data["weight"][0].replace("kg", "")),  # "weight": ["49kg"]
        "belong_to": json_data["belong_to"][0],  # "belong_to": ["東京"]
        "birth_place": json_data["birth_place"][0],  # "birth_place": ["神奈川県"]
        "debut_period": int(json_data["debut_period"][0].replace("期", "")),  # "debut_period": ["113期"]
    }

    if json_data["blood_type"][0] == "A型":  # "blood_type": ["O型"]
        i["blood_type"] = 1
    elif json_data["blood_type"][0] == "B型":
        i["blood_type"] = 2
    elif json_data["blood_type"][0] == "O型":
        i["blood_type"] = 3
    elif json_data["blood_type"][0] == "AB型":
        i["blood_type"] = 4
    else:
        raise Exception(f"Unknown blood_type: {json_data}")

    if json_data["racer_class"][0] == "A1級":  # "racer_class": ["B1級"]
        i["racer_class_type"] = 1
    elif json_data["racer_class"][0] == "A2級":
        i["racer_class_type"] = 2
    elif json_data["racer_class"][0] == "B1級":
        i["racer_class_type"] = 3
    elif json_data["racer_class"][0] == "B2級":
        i["racer_class_type"] = 4
    else:
        raise Exception(f"Unknown racer_class: {json_data}")

    racer_id_re = racer_id_pattern.search(json_data["racer_id"][0])  # "racer_id": ["4791"]
    if racer_id_re:
        i["racer_id"] = racer_id_re.group(1)
    else:
        raise Exception(f"Unknown racer_id: {json_data}")

    return i


def parse_feed_json_to_dataframe(json_data):
    L = get_logger("parse_feed_json_to_dataframe")

    # フィードjsonをdict配列に変換する
    race_bracket_items = []
    race_bracket_history_items = []
    race_info_items = []
    race_result_items = []
    race_result_start_items = []
    race_payoff_items = []
    race_odds_items = []
    racer_items = []

    for i in json_data:
        try:
            if i["url"][0].startswith("https://www.boatrace.jp/owpc/pc/race/raceindex?"):
                # NOTE: レース節データは使わない
                pass

            elif i["url"][0].startswith("https://www.boatrace.jp/owpc/pc/race/racelist?") and i["url"][0].endswith("#bracket"):
                item = parse_race_bracket(i)
                race_bracket_items.append(item)

            elif i["url"][0].startswith("https://www.boatrace.jp/owpc/pc/race/racelist?") and i["url"][0].endswith("#bracket_result"):
                item = parse_race_bracket_result(i)
                race_bracket_history_items.append(item)

            elif i["url"][0].startswith("https://www.boatrace.jp/owpc/pc/race/racelist?") and i["url"][0].endswith("#info"):
                item = parse_race_info(i)
                race_info_items.append(item)

            elif i["url"][0].startswith("https://www.boatrace.jp/owpc/pc/race/raceresult?") and i["url"][0].endswith("#result"):
                item = parse_race_result(i)
                race_result_items.append(item)

            elif i["url"][0].startswith("https://www.boatrace.jp/owpc/pc/race/raceresult?") and i["url"][0].endswith("#start"):
                item = parse_race_result_start(i)
                race_result_start_items.append(item)

            elif i["url"][0].startswith("https://www.boatrace.jp/owpc/pc/race/raceresult?") and i["url"][0].endswith("#payoff"):
                item = parse_race_payoff(i)
                race_payoff_items.append(item)

            elif i["url"][0].startswith("https://www.boatrace.jp/owpc/pc/race/odds"):
                item = parse_race_odds(i)
                if item:
                    race_odds_items.append(item)

            elif i["url"][0].startswith("https://www.boatrace.jp/owpc/pc/data/racersearch/profile?"):
                item = parse_racer_profile(i)
                if item:
                    racer_items.append(item)

            else:
                L.debug(f"Unknown type: {i}")

        except Exception as e:
            L.error(i)
            L.error(e)

    # データフレームに変換する
    if len(race_bracket_items) > 0:
        df_race_bracket = pd.DataFrame.from_dict(race_bracket_items).drop_duplicates(subset=["race_id", "racer_id"]).sort_values(["race_id", "racer_id"]).reset_index(drop=True)
    else:
        df_race_bracket = None

    if len(race_bracket_history_items) > 0:
        df_race_bracket_history = pd.DataFrame.from_dict(race_bracket_history_items).drop_duplicates(subset=["race_id", "bracket_number", "run_number"]).sort_values(["race_id", "bracket_number", "run_number"]).reset_index(drop=True)
    else:
        df_race_bracket_history = None

    if len(race_info_items) > 0:
        df_race_info = pd.DataFrame.from_dict(race_info_items).drop_duplicates(subset=["race_id"]).sort_values(["race_id"]).reset_index(drop=True)
    else:
        df_race_info = None

    if len(race_result_items) > 0:
        df_race_result = pd.DataFrame.from_dict(race_result_items).drop_duplicates(subset=["race_id", "bracket_number"]).sort_values(["race_id", "bracket_number"]).reset_index(drop=True)
    else:
        df_race_result = None

    if len(race_result_start_items) > 0:
        df_race_result_start = pd.DataFrame.from_dict(race_result_start_items).drop_duplicates(subset=["race_id", "bracket_number"]).sort_values(["race_id", "bracket_number"]).reset_index(drop=True)
    else:
        df_race_result_start = None

    if len(race_payoff_items) > 0:
        df_race_payoff = pd.DataFrame.from_dict(race_payoff_items).drop_duplicates(subset=["race_id", "bracket_number_1", "bracket_number_2", "bracket_number_3"]).sort_values(["race_id", "bracket_number_1", "bracket_number_2", "bracket_number_3"]).reset_index(drop=True)
    else:
        df_race_payoff = None

    if len(race_odds_items) > 0:
        df_race_odds = pd.DataFrame.from_dict(race_odds_items).drop_duplicates(subset=["race_id", "bet_type", "bracket_number_1", "bracket_number_2", "bracket_number_3"]).sort_values(["race_id", "bet_type", "bracket_number_1", "bracket_number_2", "bracket_number_3"]).reset_index(drop=True)
    else:
        df_race_odds = None

    if len(racer_items) > 0:
        df_racer = pd.DataFrame.from_dict(racer_items).drop_duplicates(subset=["racer_id"]).sort_values(["racer_id"]).reset_index(drop=True)
    else:
        df_racer = None

    return df_race_bracket, df_race_bracket_history, df_race_info, df_race_result, df_race_result_start, df_race_payoff, df_race_odds, df_racer
