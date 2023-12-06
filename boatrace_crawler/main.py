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


def create_racelist(s3_feed_url, target_date, s3_racelist_folder):
    L = racelist.get_logger("create_racelist")

    L.debug(f"s3_feed_url={s3_feed_url}")
    L.debug(f"target_date={target_date}")
    L.debug(f"s3_racelist_folder={s3_racelist_folder}")

    #
    L.info("# フィードをダウンロード")
    #

    json_data = racelist.get_feed(s3_client, s3_feed_url)
    L.debug(s3_feed_url)

    #
    L.info("# フィードを変換")
    #

    _, _, df_race_info, _, _, _, _, _ = racelist.parse_feed_json_to_dataframe(json_data)
    L.debug(df_race_info)

    #
    L.info("# レース一覧を抽出")
    #

    df_racelist = racelist.extract_racelist(df_race_info, target_date)
    L.debug(df_racelist)

    #
    L.info("# レース一覧をアップロード")
    #

    racelist_key = racelist.put_racelist(s3_client, df_racelist, s3_racelist_folder, target_date)
    L.debug(racelist_key)


def crawl_race(s3_racelist_folder, target_date):
    L = racelist.get_logger("crawl_race")

    L.debug(f"s3_racelist_folder={s3_racelist_folder}")
    L.debug(f"target_date={target_date}")

    #
    L.info("# レース一覧を読み込む")
    #

    df_racelist = racelist.get_racelist(s3_client, s3_racelist_folder, target_date)
    L.debug(df_racelist)

    crawl_queue = {}

    while True:
        #
        L.info("# クロール開始時刻に到達したレースを、サブプロセスでクロールする")
        #

        # まだクロールしていない、クロール開始時刻に到達した、キューに存在しないレースを抽出する
        df_racelist_not_crawl = racelist.extract_not_crawl_racelist(df_racelist, crawl_queue, datetime.now())

        for race_item in df_racelist_not_crawl.to_dict(orient="records"):
            if len(crawl_queue) < 5:
                # サブプロセスでクロールを起動して、キューに追加する
                proc = racelist.crawl_race_subprocess(race_item, f"before_{race_item['diff_minutes']}minutes")
                race_item["proc"] = proc

                crawl_queue[f"{race_item['race_id']}_before_{race_item['diff_minutes']}minutes"] = race_item

                L.debug(f"クロール起動: {race_item['race_id']}, before {race_item['diff_minutes']}minutes")

                L.debug(f"キュー: {list(crawl_queue.keys())}")

        #
        L.info("# クロール結果を確認する")
        #

        deleting_key = []

        for key, race_item in crawl_queue.items():
            if race_item["proc"].poll() is not None:
                # クロールが終了している場合、レース一覧を更新・アップロードして、キューから削除する
                L.debug(f"クロール終了: {race_item}")

                df_racelist.loc[(df_racelist["race_id"] == race_item["race_id"]) & (df_racelist["diff_minutes"] == race_item["diff_minutes"]), "crawl_datetime"] = datetime.now()

                racelist.put_racelist(s3_client, df_racelist, s3_racelist_folder, target_date)

                deleting_key.append(key)

        if len(deleting_key) > 0:
            for key in deleting_key:
                del crawl_queue[key]

            L.debug(f"キュー: {list(crawl_queue.keys())}")

        #
        L.info("# 全レースのクロールが終了した場合、ループを終了する")
        #

        if len(df_racelist) == len(df_racelist.dropna()):
            break

        time.sleep(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--task")

    args = parser.parse_args()

    if args.task == "create_racelist":
        s3_feed_url = os.environ["AWS_S3_FEED_URL"]
        target_date = datetime.strptime(os.environ["TARGET_DATE"], "%Y-%m-%d")
        s3_racelist_folder = os.environ["AWS_S3_RACELIST_FOLDER"]

        create_racelist(s3_feed_url, target_date, s3_racelist_folder)

    elif args.task == "crawl_race":
        s3_racelist_folder = os.environ["AWS_S3_RACELIST_FOLDER"]
        target_date = datetime.strptime(os.environ["TARGET_DATE"], "%Y-%m-%d")

        crawl_race(s3_racelist_folder, target_date)

    else:
        parser.print_help()
