import argparse
import os
from datetime import datetime

import racelist as racelist
from middlewares import S3Client


def create_racelist():
    L = racelist.get_logger("create_racelist")

    #
    L.info("# S3クライアントをセットアップ")
    #

    settings = {
        "AWS_ENDPOINT_URL": os.environ["AWS_ENDPOINT_URL"],
        "AWS_ACCESS_KEY_ID": os.environ["AWS_ACCESS_KEY_ID"],
        "AWS_SECRET_ACCESS_KEY": os.environ["AWS_SECRET_ACCESS_KEY"],
        "AWS_S3_CACHE_BUCKET": os.environ["AWS_S3_CACHE_BUCKET"],
    }

    s3_client = S3Client(settings)

    L.debug(s3_client)

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--task")

    args = parser.parse_args()

    if args.task == "create_racelist":
        create_racelist()

    else:
        parser.print_help()
