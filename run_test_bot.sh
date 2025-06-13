#!/usr/bin/env bash

docker stop habitbot
docker rm habitbot
docker run -d \
--name habitbot \
--restart unless-stopped \
--env-file .env \
-v "$(pwd)/db":/app \
hosstell/habitbot:latest