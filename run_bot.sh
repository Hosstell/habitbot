#!/usr/bin/env bash

docker stop habitbot
docker rm habitbot
docker build -t habitbot .
docker run \
--name habitbot \
--restart unless-stopped \
-v ./habitbot_db:/db \
--env-file .env \
habitbot:latest