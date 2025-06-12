#!/usr/bin/env bash

docker stop habitbot
docker rm habitbot
docker build -t habitbot .
docker run \
--name habitbot \
--restart unless-stopped \
--env-file .env \
habitbot:latest