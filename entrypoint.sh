#!/bin/sh
set -eu

CONFIG="${STREAMS_CONFIG:-/config/streams.conf}"
count=0

while read -r device name _rest || [ -n "$device" ]; do
  case "$device" in
    ''|\#*) continue ;;
  esac

  if [ -z "$name" ]; then
    echo "Invalid line in $CONFIG (expected: DEVICE STREAM_NAME)" >&2
    exit 1
  fi

  echo "Starting stream $name from $device"
  ffmpeg -loglevel error \
    -f v4l2 -i "$device" \
    -c:v libx264 -preset ultrafast -tune zerolatency \
    -f flv "rtmp://mediamtx:1935/$name" &
  count=$((count + 1))
done < "$CONFIG"

if [ "$count" -eq 0 ]; then
  echo "No streams defined in $CONFIG" >&2
  exit 1
fi

wait
