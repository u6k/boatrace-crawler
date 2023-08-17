import logging
import os
from distutils.util import strtobool

BOT_NAME = "boatrace_crawler"
USER_AGENT = os.environ.get("USER_AGENT", "boatrace_crawler/1.0 (+https://github.com/u6k/boatrace-crawler)")
# TODO: CRAWL_HTTP_PROXY = os.environ.get("CRAWL_HTTP_PROXY")

SPIDER_MODULES = ["boatrace_crawler.spiders"]
NEWSPIDER_MODULE = "boatrace_crawler.spiders"

ROBOTSTXT_OBEY = True

CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1
CONCURRENT_REQUESTS_PER_IP = 0

DOWNLOAD_DELAY = 1
DOWNLOAD_TIMEOUT = 60
RETRY_TIMES = 10

HTTPCACHE_ENABLED = True
# TODO: HTTPCACHE_STORAGE = "horse_racing_crawler.middlewares.S3CacheStorage"

SPIDER_CONTRACTS = {
    "boatrace_crawler.contracts.CalendarContract": 10,
}

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

logging.getLogger("boto3").setLevel(logging.INFO)
logging.getLogger("botocore").setLevel(logging.INFO)

AWS_ENDPOINT_URL = os.environ["AWS_ENDPOINT_URL"]
AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]
AWS_S3_CACHE_BUCKET = os.environ["AWS_S3_CACHE_BUCKET"]
AWS_S3_CACHE_FOLDER = os.environ["AWS_S3_CACHE_FOLDER"]

RECACHE_RACE = strtobool(os.environ.get("RECACHE_RACE", "False"))
RECACHE_DATA = strtobool(os.environ.get("RECACHE_DATA", "False"))

# TODO
# FEEDS = {
#     os.environ["AWS_S3_FEED_URL"]: {
#         "format": "json",
#         "encoding": "utf8",
#     }
# }
