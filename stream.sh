#!/bin/bash
docker compose up -d

ffmpeg -f v4l2 -i /dev/video0 \
  -c:v libx264 -preset ultrafast -tune zerolatency \
  -c:a aac -f flv rtmp://localhost:1935/mystream

