import argparse
import os
import time
from datetime import datetime

import racelist
from middlewares import S3Client

#
# S3クライアントをセットアップ
#

settings = {
    "AWS_ENDPOINT_URL": os.environ["AWS_ENDPOINT_URL"],
    "AWS_ACCESS_KEY_ID": os.environ["AWS_ACCESS_KEY_ID"],
    "AWS_SECRET_ACCESS_KEY": os.environ["AWS_SECRET_ACCESS_KEY"],
    "AWS_S3_CACHE_BUCKET": os.environ["AWS_S3_CACHE_BUCKET"],
}

s3_client = S3Client(settings)


#
# レース一覧作成
#


def create_racelist():
    L = racelist.get_logger("create_racelist")

    #
    L.info("# フィードをダウンロード")
    #

    feed_url = os.environ["AWS_S3_FEED_URL"]

    json_data = racelist.get_feed(s3_client, feed_url)

    L.debug(feed_url)

    #
    L.info("# フィードを変換")
    #

    _, _, df_race_info, _, _, _, _, _ = racelist.parse_feed_json_to_dataframe(json_data)

    L.debug(df_race_info)

    #
    L.info("# レース一覧を抽出")
    #

    target_date = datetime.strptime(os.environ["RACELIST_DATE"], "%Y-%m-%d")

    df_racelist = racelist.extract_racelist(df_race_info, target_date)

    L.debug(df_racelist)

    #
    L.info("# レース一覧をアップロード")
    #

    racelist_folder = os.environ["AWS_S3_RACELIST_FOLDER"]

    racelist_key = racelist.put_racelist(s3_client, df_racelist, racelist_folder, target_date)

    L.debug(racelist_key)


def crawl_race():
    L = racelist.get_logger("crawl_race")

    #
    L.info("# レース一覧を読み込む")
    #

    racelist_folder = os.environ["AWS_S3_RACELIST_FOLDER"]
    target_date = datetime.strptime(os.environ["RACELIST_DATE"], "%Y-%m-%d")

    df_racelist = racelist.get_racelist(s3_client, racelist_folder, target_date)

    L.debug(df_racelist)

    while True:
        df_tmp = df_racelist.dropna()

        if len(df_tmp) == len(df_racelist):
            L.info("# 全レースのクロールが終了したため、処理を終了する")
            break

        #
        L.info("# 時刻に達したレースをクロールする")
        #

        df_tmp = df_racelist.copy()
        df_tmp["now_diff_sec"] = (df_tmp["start_datetime"] - datetime.now()).dt.total_seconds()

        #
        L.info("## 30分前(1800秒前)")
        #

        file_suffix = "before_30min"
        df_races = df_tmp.query(f"crawl_timestamp_{file_suffix}.isnull() and now_diff_sec<1800")

        if len(df_races) > 0:
            dict_race = df_races.to_dict(orient="records")[0]

            racelist.crawl_race(dict_race, file_suffix)

            df_racelist.loc[df_racelist["race_id"] == dict_race["race_id"], f"crawl_timestamp_{file_suffix}"] = datetime.now()

            racelist.put_racelist(s3_client, df_racelist, racelist_folder, target_date)

        #
        L.info("## 20分前(1200秒前)")
        #

        file_suffix = "before_20min"
        df_races = df_tmp.query(f"crawl_timestamp_{file_suffix}.isnull() and now_diff_sec<1200")

        if len(df_races) > 0:
            dict_race = df_races.to_dict(orient="records")[0]

            racelist.crawl_race(dict_race, file_suffix)

            df_racelist.loc[df_racelist["race_id"] == dict_race["race_id"], f"crawl_timestamp_{file_suffix}"] = datetime.now()

            racelist.put_racelist(s3_client, df_racelist, racelist_folder, target_date)

        #
        L.info("## 15分前(900秒前)")
        #

        file_suffix = "before_15min"
        df_races = df_tmp.query(f"crawl_timestamp_{file_suffix}.isnull() and now_diff_sec<900")

        if len(df_races) > 0:
            dict_race = df_races.to_dict(orient="records")[0]

            racelist.crawl_race(dict_race, file_suffix)

            df_racelist.loc[df_racelist["race_id"] == dict_race["race_id"], f"crawl_timestamp_{file_suffix}"] = datetime.now()

            racelist.put_racelist(s3_client, df_racelist, racelist_folder, target_date)

        #
        L.info("## 10分前(600秒前)")
        #

        file_suffix = "before_10min"
        df_races = df_tmp.query(f"crawl_timestamp_{file_suffix}.isnull() and now_diff_sec<600")

        if len(df_races) > 0:
            dict_race = df_races.to_dict(orient="records")[0]

            racelist.crawl_race(dict_race, file_suffix)

            df_racelist.loc[df_racelist["race_id"] == dict_race["race_id"], f"crawl_timestamp_{file_suffix}"] = datetime.now()

            racelist.put_racelist(s3_client, df_racelist, racelist_folder, target_date)

        #
        L.info("## 5分前(300秒前)")
        #

        file_suffix = "before_5min"
        df_races = df_tmp.query(f"crawl_timestamp_{file_suffix}.isnull() and now_diff_sec<300")

        if len(df_races) > 0:
            dict_race = df_races.to_dict(orient="records")[0]

            racelist.crawl_race(dict_race, file_suffix)

            df_racelist.loc[df_racelist["race_id"] == dict_race["race_id"], f"crawl_timestamp_{file_suffix}"] = datetime.now()

            racelist.put_racelist(s3_client, df_racelist, racelist_folder, target_date)

        #
        L.info("## 2分前(120秒前)")
        #

        file_suffix = "before_2min"
        df_races = df_tmp.query(f"crawl_timestamp_{file_suffix}.isnull() and now_diff_sec<120")

        if len(df_races) > 0:
            dict_race = df_races.to_dict(orient="records")[0]

            racelist.crawl_race(dict_race, file_suffix)

            df_racelist.loc[df_racelist["race_id"] == dict_race["race_id"], f"crawl_timestamp_{file_suffix}"] = datetime.now()

            racelist.put_racelist(s3_client, df_racelist, racelist_folder, target_date)

        #
        L.info("# 10秒間スリープする")
        #

        time.sleep(10)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--task")

    args = parser.parse_args()

    if args.task == "create_racelist":
        create_racelist()

    elif args.task == "crawl_race":
        crawl_race()

    else:
        parser.print_help()
