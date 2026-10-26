# Troubleshooting

## `ffmpeg` or `ffprobe` is not found

Install FFmpeg and ensure both executables are on `PATH`:

```bash
ffmpeg -version
ffprobe -version
```

Restart the terminal or Hermes after changing `PATH`.

## Python reports a missing package

Install the repository requirements into the same interpreter used to run the script:

```bash
python -m pip install -r requirements.txt
python -c "import PIL, reportlab, pypdf, yt_dlp; print('dependencies OK')"
```

If Hermes has its own production Python environment, do not modify it. Use a project virtual environment or `uv`.

## SharePoint URL fails in `yt-dlp`

This is expected for most authenticated SharePoint pages. Open the page in the logged-in browser, download the recording and transcript, and pass their local paths to `prepare`.

Do not solve this by exporting cookies or putting access tokens in command history.

## No transcript was produced

Possible causes:

- The source has no subtitles.
- Teams or Zoom has not generated the transcript yet.
- The user does not have permission to download it.
- The transcript language is not English; automatic remote subtitle retrieval currently requests English.

Download or generate a transcript separately, then place it in the run directory. Frame extraction can still run without one, but content-complete notes require transcript or audio analysis.

## No candidate frames were created

Check that the video is readable:

```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "recording.mp4"
```

Then rerun with a positive interval. A corrupt file, unsupported codec, zero-length recording, or inaccessible path can prevent extraction.

## Too many candidate frames

Increase `--interval`:

```bash
python scripts/visual_notes.py prepare "recording.mp4" --workdir "runs/example" --interval 15
```

Use a shorter interval only for fast demos or frequent slide changes.

## A brief slide is missing

Use the transcript timestamp and extract a precise frame:

```bash
ffmpeg -y -ss 00:12:34 -i "recording.mp4" -frames:v 1 "selected-1234.jpg"
```

Add that image directly to the manifest.

## Manifest validation fails

Common causes:

- `slides` is empty.
- A slide lacks `timestamp`, `title`, `image`, `notes`, or `why_it_matters`.
- `notes` is not a non-empty JSON array.
- The image path does not exist relative to the manifest.
- The timestamp format is invalid.
- Crop bounds are reversed or incomplete.

See [MANIFEST.md](MANIFEST.md) for the schema and examples.

## Notes overlap or disappear in a wide layout

The wide layout has less vertical room for notes. Switch to `standard`, shorten the bullets, or split a dense concept into a separate content-driven page. Always inspect the rendered PDF.

## The PDF has one more page than expected

That is correct. The builder creates one cover page plus one page per selected manifest item.

## Tests fail on the generated-video test

The local-recording test invokes FFmpeg to create a two-second MP4. Confirm FFmpeg is installed and available to the test process. Run the failing command with `pytest -vv` for details:

```bash
python -m pytest scripts/test_visual_notes.py -vv
```
