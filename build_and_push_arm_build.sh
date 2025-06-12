#!/usr/bin/env bash

set -e

docker build -t hosstell/habitbot::latest .
docker image push hosstell/habitbot:latest