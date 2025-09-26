# 競艇データクローラー _(boatrace-crawler)_

[![build](https://github.com/u6k/boatrace-crawler/actions/workflows/build.yml/badge.svg)](https://github.com/u6k/boatrace-crawler/actions/workflows/build.yml)
[![license](https://img.shields.io/github/license/u6k/boatrace-crawler.svg)](https://github.com/u6k/boatrace-crawler/blob/master/LICENSE)
[![GitHub release](https://img.shields.io/github/release/u6k/boatrace-crawler.svg)](https://github.com/u6k/boatrace-crawler/releases)
[![WebSite](https://img.shields.io/website-up-down-green-red/https/shields.io.svg?label=u6k.Redmine)](https://redmine.u6k.me/projects/boatrace-crawler)
[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)

> 競艇データをクロールする

## Install

Dockerとdocker composeを使用する。

```bash
$ docker version
Client: Docker Engine - Community
 Version:           24.0.2
 API version:       1.43
 Go version:        go1.20.4
 Git commit:        cb74dfc
 Built:             Thu May 25 21:51:00 2023
 OS/Arch:           linux/amd64
 Context:           default

Server: Docker Engine - Community
 Engine:
  Version:          24.0.2
  API version:      1.43 (minimum version 1.12)
  Go version:       go1.20.4
  Git commit:       659604f
  Built:            Thu May 25 21:51:00 2023
  OS/Arch:          linux/amd64
  Experimental:     false
 containerd:
  Version:          1.6.21
  GitCommit:        3dce8eb055cbb6872793272b4f20ed16117344f8
 runc:
  Version:          1.1.7
  GitCommit:        v1.1.7-0-g860f061
 docker-init:
  Version:          0.19.0
  GitCommit:        de40ad0
```

```bash
$ docker compose version
Docker Compose version v2.18.1
```

ビルド済みDockerイメージを使用する場合、`docker pull`する。

```bash
docker pull ghcr.io/u6k/boatrace-crawler
```

Dockerイメージをビルドする場合、docker composeでbuildする。

```bash
docker compose build
```

Linuxに直接セットアップする場合、`Dockerfile`を参照すること。

## Usage

クローラーを起動する。

```bash
docker compose up
```

RabbitMQからメッセージを受信してクロールを開始する。MQに投入するメッセージは以下の形式。

```
{
"start_url": "https://www.boatrace.jp/owpc/pc/race/index?hd=20250926",
"AWS_S3_FEED_URL": "s3://boatrace/feed/calendar/calendar_20250926.json",
"RECACHE_RACE": "True",
"RECACHE_DATA": "False"
}
```

## Other

最新情報は[Wiki - boatrace-crawler - u6k.Redmine](https://redmine.u6k.me/projects/boatrace-crawler/wiki/Wiki)を参照すること。

## Maintainer

- u6k
    - [Twitter](https://twitter.com/u6k_yu1)
    - [GitHub](https://github.com/u6k)
    - [Blog](https://blog.u6k.me/)

## Contributing

当プロジェクトに興味を持っていただき、ありがとうございます。[既存のチケット](https://redmine.u6k.me/projects/boatrace-crawler/issues)をご覧ください。

当プロジェクトは、[Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/)に準拠します。

## License

[MIT License](https://github.com/u6k/boatrace-crawler/blob/main/LICENSE)
