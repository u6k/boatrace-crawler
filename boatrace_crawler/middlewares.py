# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html


import io
from pathlib import Path

import boto3
import joblib
from botocore.exceptions import ClientError
from scrapy.http import Headers
from scrapy.responsetypes import responsetypes


class S3Client:
    def __init__(self, settings):
        self.s3_endpoint = settings["AWS_ENDPOINT_URL"]
        self.s3_access_key = settings["AWS_ACCESS_KEY_ID"]
        self.s3_secret_key = settings["AWS_SECRET_ACCESS_KEY"]
        self.s3_bucket = settings["AWS_S3_CACHE_BUCKET"]

        self.s3_client = boto3.resource("s3", endpoint_url=self.s3_endpoint, aws_access_key_id=self.s3_access_key, aws_secret_access_key=self.s3_secret_key)

        self.s3_bucket_obj = self.s3_client.Bucket(self.s3_bucket)
        if not self.s3_bucket_obj.creation_date:
            self.s3_bucket_obj.create()

    def get(self, key):
        s3_obj = self.s3_bucket_obj.Object(key)

        try:
            with io.BytesIO(s3_obj.get()["Body"].read()) as b:
                data = joblib.load(b)
        except ClientError as err:
            if err.response["Error"]["Code"] == "404" or err.response["Error"]["Code"] == "NoSuchKey":
                data = None
            else:
                raise err

        return data

    def put(self, key, data_bytes):
        self.s3_bucket_obj.Object(key).put(Body=data_bytes)


class S3CacheStorage:
    def __init__(self, settings):
        # Store parameters
        self.s3_folder = settings["AWS_S3_CACHE_FOLDER"]

        self.recache_race = settings["RECACHE_RACE"]
        self.recache_data = settings["RECACHE_DATA"]

        # Setup s3 client
        self.s3_client = S3Client(settings)

    def open_spider(self, spider):
        self._fingerprinter = spider.crawler.request_fingerprinter

    def close_spider(self, spider):
        pass

    def retrieve_response(self, spider, request):
        spider.logger.debug(f"#retrieve_response: start: url={request.url}")

        # 再キャッシュする
        if self.recache_race and request.url.startswith("https://www.boatrace.jp/owpc/pc/race/"):
            spider.logger.debug("#retrieve_response: re-cache race")
            return

        if self.recache_data and request.url.startswith("https://www.boatrace.jp/owpc/pc/data/"):
            spider.logger.debug("#retrieve_response: re-cache data")
            return

        # キャッシュから取得する
        rpath = self._get_request_path(spider, request)
        spider.logger.debug(f"#retrieve_response: cache path={rpath}")

        data = self.s3_client.get(rpath + ".joblib")
        if data is None:
            spider.logger.debug("#retrieve_response: cache not found")
            return

        url = data["response"]["url"]
        status = data["response"]["status"]
        headers = Headers(data["response"]["headers"])
        body = data["response"]["body"]
        respcls = responsetypes.from_args(headers=headers, url=url)
        response = respcls(url=url, headers=headers, status=status, body=body)

        spider.logger.debug("#retrieve_response: cache exist")

        return response

    def store_response(self, spider, request, response):
        spider.logger.debug(f"#store_response: start: url={response.url}, status={response.status}")

        rpath = self._get_request_path(spider, request)
        spider.logger.debug(f"#store_response: cache path={rpath}")

        data = {
            "request": {
                "url": request.url,
                "method": request.method,
                "headers": request.headers,
                "body": request.body,
            },
            "response": {
                "url": response.url,
                "status": response.status,
                "headers": response.headers,
                "body": response.body,
            },
        }

        with io.BytesIO() as b:
            joblib.dump(data, b, compress=True)

            self.s3_client.put(rpath + ".joblib", b.getvalue())

    def _get_request_path(self, spider, request):
        key = self._fingerprinter.fingerprint(request).hex()
        path = str(Path(self.s3_folder, spider.name, key[0:2], key))

        return path
