---
sidebar_position: 6
---

# Livestream

Use this setup when a PUDA machine host has one or more USB cameras, webcams, or IP cameras and you want live video available over RTSP, RTMP, HLS, or WebRTC.

This guide assumes:

- Docker Engine and Docker Compose are installed.
- A USB camera, webcam, or IP camera is available to the host.
- The host can be reached by operators, preferably over the same Tailscale network used for PUDA.

## Find camera devices

On the livestream host, list video devices:

```bash
ls -l /dev/video*
```

If the machine has `v4l-utils` installed, inspect the cameras:

```bash
v4l2-ctl --list-devices
```

Choose the device paths to expose, such as `/dev/video0` and `/dev/video2`.

For IP cameras, find the camera stream URL from the camera admin UI or vendor docs. RTSP URLs usually look like:

```text
rtsp://user:pass@192.168.1.50:554/stream1
```

## Set up the configuration files

Navigate to the livestream directory:

```bash
cd edge/livestream
```

You will create three files: `.env` for the WebRTC host address, `streams.conf` to define your cameras, and `entrypoint.sh` to start them. `compose.yml` stays unchanged regardless of how many cameras you have.

Create `.env`:

```env
# Host address advertised for WebRTC. Use the Tailscale IP or DNS name.
TAILSCALE_IP=100.64.0.10
```

Create `streams.conf`. Each non-blank, non-comment line defines one stream: the input and the public stream name, separated by whitespace. The input can be a local `/dev/video*` device or an IP camera URL.

```conf
# input                                      stream name
/dev/video0                                 cam0
/dev/video2                                 cam1
rtsp://user:pass@192.168.1.50:554/stream1  ipcam0
```

To add or remove a camera later, edit `streams.conf` and run:

```bash
docker compose restart ffmpeg
```

Create `entrypoint.sh`:

```bash
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
```

## Create the Compose file

Create `compose.yml`:

```yaml
services:
  mediamtx:
    image: bluenviron/mediamtx:latest
    container_name: mediamtx
    ports:
      - "8554:8554" # RTSP
      - "1935:1935" # RTMP
      - "8888:8888" # HLS
      - "8889:8889" # WebRTC HTTP/WHIP/WHEP
      - "8189:8189/udp" # WebRTC ICE/UDP
      - "8189:8189/tcp" # WebRTC ICE/TCP
    environment:
      - MTX_WEBRTC=yes
      - MTX_WEBRTCADDRESS=:8889
      - MTX_WEBRTCLOCALUDPADDRESS=:8189
      - MTX_WEBRTCADDITIONALHOSTS=${TAILSCALE_IP}
    restart: unless-stopped

  ffmpeg:
    image: linuxserver/ffmpeg:latest
    container_name: ffmpeg
    depends_on:
      - mediamtx
    device_cgroup_rules:
      - "c 81:* rmw" # video4linux: allow any /dev/video* device
    group_add:
      - video
    volumes:
      - ./streams.conf:/config/streams.conf:ro
      - ./entrypoint.sh:/entrypoint.sh:ro
    entrypoint: ["/bin/sh", "/entrypoint.sh"]
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    restart: unless-stopped
```

If a port is already in use on the host, change the left-hand side of the matching `ports` entry in `compose.yml`.

## Start the livestream

```bash
docker compose up -d
```

Check that both services are running:

```bash
docker compose ps
```

View logs if a stream does not appear:

```bash
docker compose logs -f mediamtx ffmpeg
```

## Stream URLs

For each stream name in `streams.conf`, replace `STREAM_NAME` and `100.64.0.10` with your values:

| Protocol | URL |
| --- | --- |
| RTSP | `rtsp://100.64.0.10:8554/STREAM_NAME` |
| RTMP | `rtmp://100.64.0.10:1935/STREAM_NAME` |
| HLS | `http://100.64.0.10:8888/STREAM_NAME/` |
| WebRTC | `http://100.64.0.10:8889/STREAM_NAME/` |

With the example `streams.conf`, `cam0`, `cam1`, and `ipcam0` are available at those URLs.

## Verify with ffprobe

From another machine that can reach the livestream host, verify a stream:

```bash
ffprobe rtsp://100.64.0.10:8554/cam0
```

For browser viewing, open the HLS or WebRTC URL.
