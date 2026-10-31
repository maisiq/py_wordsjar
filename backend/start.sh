#!/bin/bash

uvicorn --reload \
 --host 0.0.0.0 \
 --port 8080 \
 --factory main:init \
 --workers 1 \
 --limit-concurrency 200 \
 --backlog 128 \
 --timeout-keep-alive 5