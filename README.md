# Visual Video Notes skill for Hermes Agent

A portable Hermes skill that turns YouTube videos, local recordings, and downloaded private meeting recordings into visual-notes PDFs and selected-frame ZIPs.

## Supported sources

- YouTube videos and channels
- Local video files
- Teams or Zoom recordings downloaded from SharePoint, OneDrive, or another authenticated service
- Optional VTT, SRT, or TXT transcripts

Authenticated recordings are downloaded through the user's logged-in browser. The skill never exports browser cookies, Microsoft credentials, or access tokens.

## Install

1. Install [Hermes Agent](https://hermes-agent.nousresearch.com/docs).
2. Copy the `youtube-visual-speaker-notes` directory into your active profile's `skills/media/` directory.
3. Install FFmpeg so `ffmpeg` and `ffprobe` are on `PATH`.
4. Create an isolated Python environment and install the dependencies:

```bash
python -m venv .venv
# Windows: .venv\Scripts\python -m pip install -r requirements.txt
# macOS/Linux: .venv/bin/python -m pip install -r requirements.txt
```

Start a new Hermes session after installation so the skill catalog reloads.

## Test

```bash
python -m pytest scripts/test_visual_notes.py -q
```

The suite creates a tiny local MP4 with FFmpeg and verifies local-recording preparation, transcript handling, PDF generation, and timestamp parsing.

## Privacy

SharePoint, Teams, Zoom, OneDrive, and local-file sources are private by default. Do not publish recordings, transcripts, screenshots, links, or derived notes without explicit permission.

## License

MIT
