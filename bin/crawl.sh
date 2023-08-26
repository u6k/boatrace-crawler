#!/bin/bash -eu

tor &
sleep 120

privoxy /etc/privoxy/config &
sleep 10

curl -x 127.0.0.1:8118 httpbin.org/get

scrapy crawl boatrace_spider $@
