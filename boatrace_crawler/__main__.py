import json
import logging
import logging.config
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor

import pika

logging.config.fileConfig("logging.conf")
L = logging.getLogger("boatrace.mq")

executor = ThreadPoolExecutor(max_workers=None)


def crawl_process(body, delivery_tag):
    logger = logging.getLogger(f"boatrace.mq.{delivery_tag}")
    logger.info(f"crawl_process: {body=}")

    try:
        msg = json.loads(body.decode())
        start_url = msg["start_url"]

        # 環境変数を取得する
        crawl_env = os.environ.copy()
        for k, v in msg.items():
            crawl_env[k] = v

        # クロール用プロセスを開始する
        args = ["scrapy", "crawl", "boatrace_spider", "-a", f"start_url={start_url}"]
        logger.debug(f"{args=}")

        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=crawl_env,
        )
        logger.debug("subprocess starting")

        while True:
            output = proc.stdout.readline().decode("utf8").rstrip()
            if not output and proc.poll() is not None:
                break

            logger.debug(output)

        logger.info(f"crawl finish: {proc.returncode=}")
    except:  # noqa
        logger.exception("crawl_process: error")


def mq_callback(ch, method, properties, body):
    L.info(f"process: {method=}, {body=}")

    try:
        executor.submit(crawl_process, body, method.delivery_tag)

        ch.basic_ack(method.delivery_tag)
        L.info("acked")
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
