# Complete usage guide

## Workflow overview

The helper has two commands:

1. `prepare` gathers metadata, extracts timestamped frames, creates contact sheets, and writes a manifest template.
2. `build` validates a completed manifest, generates the PDF, and optionally packages selected screenshots.

The script does not automatically decide which visuals are important or write the notes. That editorial stage is performed by Hermes using the transcript, contact sheets, and `SKILL.md` rules.

## Command reference

```text
visual_notes.py prepare SOURCE --workdir DIRECTORY [options]
visual_notes.py build MANIFEST --output PDF [--zip ZIP]
```

### `prepare`

| Argument | Required | Meaning |
|---|---:|---|
| `SOURCE` | Yes | YouTube URL, supported public video URL, channel URL, or local video path |
| `--workdir` | Yes | Isolated directory for metadata, frames, contact sheets, and the manifest template |
| `--interval` | No | Seconds between candidate frames; default is `8` |
| `--transcript` | No | Local VTT, SRT, or TXT transcript copied into the run directory |
| `--title` | No | Overrides the detected title |
| `--source-url` | No | Records the original page URL in metadata and the PDF footer |

### `build`

| Argument | Required | Meaning |
|---|---:|---|
| `MANIFEST` | Yes | Completed JSON manifest |
| `--output` | Yes | Destination PDF |
| `--zip` | No | Destination ZIP for cropped selected frames and `index.csv` |

## Example 1: YouTube video

```bash
python scripts/visual_notes.py prepare \
  "https://www.youtube.com/watch?v=VIDEO_ID" \
  --workdir "runs/youtube-demo" \
  --interval 8
```

Expected preparation output:

```text
runs/youtube-demo/
├── metadata.json
├── video.mp4
├── transcript.en.vtt        # when subtitles are available
├── candidates/
├── contact_sheets/
└── manifest.template.json
```

For a channel URL, `prepare` resolves the latest upload:

```bash
python scripts/visual_notes.py prepare \
  "https://www.youtube.com/@CHANNEL/videos" \
  --workdir "runs/latest-upload"
```

## Example 2: Teams recording stored in SharePoint

### Acquire the files

1. Open the SharePoint recording in the user's logged-in browser.
2. Download the MP4 using the page's download control.
3. Download the transcript if Teams exposes one. VTT is preferred, but SRT or TXT is accepted.
4. Keep both files in a private local directory.

Do not extract browser cookies or paste Microsoft access tokens into a command. A SharePoint page URL is normally not a direct media URL.

### Prepare the recording

```bash
python scripts/visual_notes.py prepare \
  "C:/Users/me/Downloads/architecture-review.mp4" \
  --transcript "C:/Users/me/Downloads/architecture-review.vtt" \
  --source-url "https://contoso.sharepoint.com/:v:/r/sites/team/..." \
  --title "Architecture review — checkout modernization" \
  --workdir "C:/Users/me/visual-notes/architecture-review" \
  --interval 6
```

Use a shorter interval for meetings with quick screen changes. The original MP4 stays in place; only metadata, the optional transcript copy, candidate frames, and contact sheets are written to `--workdir`.

### Meeting-specific editorial checklist

When supported by the recording or transcript, capture:

- Decisions and their rationale
- Action items, named owners, and dates
- Unresolved questions and dependencies
- Risks, assumptions, and caveats
- Architecture diagrams, dashboards, demos, or code that clarify the discussion

Do not infer an owner or deadline when none was stated. Keep uncertainty next to the affected item.

## Example 3: Local MP4 without a transcript

```bash
python scripts/visual_notes.py prepare "demo.mp4" \
  --title "Agent workflow demo" \
  --workdir "runs/agent-demo"
```

The frame workflow still works, but complete notes require a transcript. Create one with an available speech-to-text tool, then place it in the run directory before drafting the manifest.

## Example 4: Zoom recording

Download the MP4 and transcript from Zoom, then use the same local-file workflow:

```bash
python scripts/visual_notes.py prepare "downloads/customer-discovery.mp4" \
  --transcript "downloads/customer-discovery.vtt" \
  --title "Customer discovery" \
  --source-url "https://zoom.us/rec/share/..." \
  --workdir "runs/customer-discovery"
```

## Choosing the frame interval

| Video type | Suggested interval |
|---|---:|
| Mostly static presentation | 10–15 seconds |
| Typical talk or meeting | 6–10 seconds |
| Fast demo or rapid slide changes | 2–5 seconds |

A fixed interval can miss a brief slide. Use transcript timestamps and extract an exact nearby frame when the contact sheets do not contain the needed visual:

```bash
ffmpeg -y -ss 00:12:34 -i "recording.mp4" -frames:v 1 "selected-1234.jpg"
```

## Reviewing contact sheets

Review every sheet rather than stopping after the first few. Select visuals that carry unique information:

- Architecture or process diagrams
- Tables, charts, benchmarks, and dashboards
- Complete slide builds
- Code or configuration needed to understand a workflow
- UI states that demonstrate a meaningful step

Exclude:

- Repeated animation states when the final state is sufficient
- Presenter-only frames
- Holding screens, logos, and title cards without content
- Sponsor or promotional segments
- Memes and decorative visuals that do not improve understanding

## Completing the manifest

Copy the generated template:

```bash
cp "runs/example/manifest.template.json" "runs/example/manifest.json"
```

On Windows, use File Explorer or another file-copy command available in the active shell. See [MANIFEST.md](MANIFEST.md) for every field and a complete example.

## Building the PDF and ZIP

```bash
python scripts/visual_notes.py build "runs/example/manifest.json" \
  --output "runs/example/visual-notes.pdf" \
  --zip "runs/example/selected-frames.zip"
```

The PDF contains one cover page plus one page per manifest item. The ZIP contains each selected or cropped image plus `index.csv` with order, timestamp, title, and filename.

## Quality assurance

Before delivery:

1. Confirm PDF page count equals `1 + number of slides`.
2. Extract PDF text and confirm every manifest title appears.
3. Confirm the ZIP contains one image per slide plus `index.csv`.
4. Render and inspect every PDF page.
5. Fix clipped titles, unreadable labels, bad crops, overlapping notes, or hidden bullets.
6. For private sources, ensure outputs remain in an approved private location.
