import json
import logging
import logging.config
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor

import pika

logging.config.fileConfig("logging.conf")
L = logging.getLogger("boatrace.mq")

executor = ThreadPoolExecutor(max_workers=1)


def crawl_process(body):
    L.info(f"crawl_process: {body=}")

    try:
        msg = json.loads(body.decode())
        start_url = msg["start_url"]

        # 環境変数を取得する
        crawl_env = os.environ.copy()
        for k, v in msg.items():
            crawl_env[k] = v

        # クロール用プロセスを開始する
        result = subprocess.run(["scrapy", "crawl", "boatrace_spider", "-a", f"start_url={start_url}"], env=crawl_env)
        L.info(f"crawl finish: {result.returncode=}")
    except:  # noqa
        L.exception("crawl_process: error")


def ack_message(ch, delivery_tag):
    L.info(f"ack_message: {delivery_tag=}")

    try:
        ch.basic_ack(delivery_tag)

        L.info("acked")
    except:  # noqa
        L.exception("acked: error")


def mq_callback(ch, method, properties, body):
    L.info(f"process: {method=}, {body=}")

    try:
        future = executor.submit(crawl_process, body)

        def ack_callback(f): return mq_conn.add_callback_threadsafe(lambda: ack_message(ch, method.delivery_tag))
        future.add_done_callback(ack_callback)
    except:  # noqa
        L.exception("process: error")


if __name__ == "__main__":
    mq_url = os.environ["MQ_URL"]
    mq_queue = os.environ["MQ_QUEUE"]

    L.info(f"{mq_url=}")
    L.info(f"{mq_queue=}")

    mq_conn = pika.BlockingConnection(pika.URLParameters(mq_url))
    mq_channel = mq_conn.channel()
    mq_channel.queue_declare(queue=mq_queue, durable=True)
    mq_channel.basic_qos(prefetch_count=1)
    mq_channel.basic_consume(queue=mq_queue, on_message_callback=mq_callback, auto_ack=False)

    try:
        L.info("start consuming")
        mq_channel.start_consuming()
    except:  # noqa
        L.exception("consuming: error")
    finally:
        mq_conn.close()
