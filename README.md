# Visual Video Notes skill for Hermes Agent

A portable [Hermes Agent](https://hermes-agent.nousresearch.com/docs) skill that converts videos into content-driven visual notes. It extracts candidate frames, helps an agent select meaningful visuals, and builds a landscape PDF plus an optional ZIP of the selected screenshots.

## What it supports

| Source | How it is handled |
|---|---|
| YouTube video | Downloaded with `yt-dlp`; English subtitles are requested when available |
| YouTube channel | The latest upload is resolved and prepared |
| Local recording | Read directly without copying the source video |
| Teams/SharePoint/OneDrive | Download through the authenticated browser, then process as a local file |
| Zoom or other meeting recording | Download or export the recording, then process as a local file |
| Transcript | Optional VTT, SRT, or TXT file copied into the run directory |

> [!IMPORTANT]
> A private SharePoint page is not treated as a direct media URL. Download it through the user's authenticated browser. The skill does not export cookies, tokens, or Microsoft credentials.

## Outputs

- `metadata.json` — source metadata and duration
- `candidates/` — timestamped candidate frames
- `contact_sheets/` — review sheets for visual selection
- `manifest.template.json` — starting point for the final notes
- A generated visual-notes PDF
- An optional ZIP containing selected screenshots and `index.csv`

The number of pages is content-driven. Repeated animation states, presenter-only shots, title cards, promotional material, and filler should be excluded.

## Quick start

### 1. Install the skill

Clone or copy this repository to the active Hermes profile:

```text
<HERMES_HOME>/skills/media/youtube-visual-speaker-notes/
```

`HERMES_HOME` is normally `~/.hermes`. Profiles use their own home directory. Start a new Hermes session after installation so the skill catalog reloads.

### 2. Install runtime dependencies

Install Python 3.10 or later plus [FFmpeg](https://ffmpeg.org/) so both `ffmpeg` and `ffprobe` are on `PATH`.

With `uv`:

```bash
uv venv
uv pip install -r requirements.txt
```

With standard Python:

```bash
python -m venv .venv
# Windows
.venv/Scripts/python.exe -m pip install -r requirements.txt
# macOS/Linux
.venv/bin/python -m pip install -r requirements.txt
```

### 3. Prepare a source

YouTube:

```bash
python scripts/visual_notes.py prepare "https://www.youtube.com/watch?v=VIDEO_ID" \
  --workdir "runs/example" \
  --interval 8
```

Downloaded Teams recording with transcript:

```bash
python scripts/visual_notes.py prepare "downloads/architecture-review.mp4" \
  --transcript "downloads/architecture-review.vtt" \
  --source-url "https://contoso.sharepoint.com/:v:/r/..." \
  --title "Architecture review" \
  --workdir "runs/architecture-review" \
  --interval 8
```

### 4. Select frames and write the manifest

Review every image under `contact_sheets/`. Copy `manifest.template.json` to `manifest.json`, then add one item for every unique substantive visual. Each item needs a timestamp, title, image, notes, and core idea.

### 5. Build the deliverables

```bash
python scripts/visual_notes.py build "runs/architecture-review/manifest.json" \
  --output "runs/architecture-review/visual-notes.pdf" \
  --zip "runs/architecture-review/selected-frames.zip"
```

## Documentation

- [Complete usage guide](docs/USAGE.md)
- [Manifest reference](docs/MANIFEST.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Example Teams meeting manifest](examples/teams-meeting.manifest.json)
- [Hermes workflow and editorial rules](SKILL.md)

## Tests

```bash
python -m pytest scripts/test_visual_notes.py -q
```

The suite creates a tiny MP4 with FFmpeg and verifies local-recording preparation, transcript handling, timestamp parsing, manifest validation, and PDF generation.

## Privacy and publishing

SharePoint, Teams, Zoom, OneDrive, and local-file sources are private by default. Do not publish recordings, transcripts, screenshots, source links, or derived notes without explicit permission and confirmed redistribution rights. Public YouTube content may still have copyright restrictions.

## License

[MIT](LICENSE)
