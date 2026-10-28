# Telegram Video Uploader

An unattended Telegram userbot that scans a mounted video directory, prepares files as H.264/AAC MP4, uploads them to the General forum topic, copies each post into a configured topic, and archives successfully uploaded originals beside their source files.

## Requirements

- Docker Engine and Docker Compose
- A running Tor container named `tor`, with its SOCKS5 listener available at `127.0.0.1:9050`
- Telegram API credentials from <https://my.telegram.org>
- A Telegram account that can post in the target group and its topics

The uploader shares the network namespace of the existing `tor` container. Start Tor before starting the uploader. Since both containers share localhost, Tor must listen on port `9050` in that namespace.

## Configuration

Copy `.env.example` to `.env` and set:

- `API_ID` and `API_HASH`: Telegram application credentials
- `CHAT_ID`: numeric group ID, for example `-1001234567890`
- `THREAD_ID`: set to `1` for the General topic
- `FORWARD_THREAD_ID`: destination topic ID in the same group
- `SRC_VIDEOS_DIR`: absolute path to the host video directory; on Windows, prefer forward slashes, for example `C:/Users/name/Videos`

The host path is mounted at `/app/videos` inside the container. Originals are moved to `uploaded_archive` inside each source folder after every part has been uploaded and copied. Temporary media is created under `tmp_chunks` and removed when processing completes or fails. Leftovers from an abrupt container stop are cleared at the next startup. The `data` mount stores the Telethon login session.

## Run

On first startup, run in the foreground so Telethon can request the account phone number and login code:

```sh
docker compose up --build
```

After the session has been created in `data`, stop the foreground process and run it in the background:

```sh
docker compose up -d
docker compose logs -f uploader
```

The service scans after startup and then every 600 seconds. It retries files that fail on a later scan. Stop it with `docker compose down`.

## Processing behavior

- Scans recursively and sorts video paths alphabetically, ignoring `uploaded_archive` and `tmp_chunks` directories.
- Leaves H.264 MP4 files unchanged, remuxes H.264 in other containers, and transcodes other video codecs with libx264 CRF 22 / fast preset and AAC 128 kbit/s.
- Splits outputs above 3.9 GiB using stream copy. Each produced segment is checked against the size limit; segment duration is reduced and retried if any segment is too large.
- Uploads to `THREAD_ID`, then sends the returned Telegram media as a new message in `FORWARD_THREAD_ID` so the copied post has no forward attribution.
- Archives the original only after every upload and topic copy succeeds.

The account must be eligible to upload files of this size. Telegram limits and account eligibility may change independently of this application.

## Local tests

```sh
python3 -m unittest discover -s tests -v
```