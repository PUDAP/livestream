#!/bin/sh
set -eu

CONFIG="${STREAMS_CONFIG:-/config/streams.conf}"
count=0

while read -r input name _rest || [ -n "$input" ]; do
  case "$input" in
    ''|\#*) continue ;;
  esac

  if [ -z "$name" ]; then
    echo "Invalid line in $CONFIG (expected: INPUT STREAM_NAME)" >&2
    exit 1
  fi

  echo "Starting stream $name from $input"
  case "$input" in
    /dev/video*)
      ffmpeg -loglevel error \
        -f v4l2 -i "$input" \
        -c:v libx264 -preset ultrafast -tune zerolatency \
        -f flv "rtmp://mediamtx:1935/$name" &
      ;;
    rtsp://*)
      ffmpeg -loglevel error \
        -rtsp_transport tcp -i "$input" \
        -c:v copy \
        -f flv "rtmp://mediamtx:1935/$name" &
      ;;
    *)
      ffmpeg -loglevel error \
        -i "$input" \
        -c:v copy \
        -f flv "rtmp://mediamtx:1935/$name" &
      ;;
  esac
  count=$((count + 1))
done < "$CONFIG"

if [ "$count" -eq 0 ]; then
  echo "No streams defined in $CONFIG" >&2
  exit 1
fi

wait
