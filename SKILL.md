---
name: youtube-visual-speaker-notes
description: Create visual notes from videos and private recordings.
version: 0.1.0
author: Ira, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [YouTube, PDF, Slides, Visual Notes, Telegram]
    related_skills: [youtube-content, pdf]
---

# Visual Video Notes

Turn a YouTube video, local recording, or downloaded private meeting into complete, easy-to-read notes with selected frames and an optional ZIP of the chosen images. The notes should work either after watching or instead of watching: preserve the full conceptual thread, concrete steps, examples, caveats, decisions, and conclusions without reproducing the transcript. Output length follows the substance of the source; never impose a fixed slide or page count.

## When to Use

- A message contains a YouTube video, channel, `/videos`, or `youtu.be` URL and asks for notes, a PDF, screenshots, or extraction.
- The user provides a local video, downloaded Teams/Zoom recording, or an authenticated SharePoint/OneDrive recording link.
- A Telegram message is only a YouTube URL: treat that as a request to run this workflow automatically.
- The user wants screenshots paired with transcript-derived notes.
- Don't use for audio-only summaries with no useful visuals; use a transcript-summary workflow instead.

## Prerequisites

Use an isolated helper environment with Python 3.10+, `Pillow`, `reportlab`, `pypdf`, and `pytest`; add `yt-dlp` when processing YouTube or another supported public URL. `ffmpeg` and `ffprobe` must be on PATH. Do not install packages into Hermes's production environment.

The helper is `scripts/visual_notes.py`. Resolve the skill directory at runtime with `skill_view`; never hardcode a user's home directory. On Windows the venv interpreter is `Scripts/python.exe`; on Linux/macOS it is `bin/python`.

For authenticated SharePoint or OneDrive sources, use the logged-in browser to download the recording and, when available, its `.vtt`, `.srt`, or `.txt` transcript. Never copy browser cookies, access tokens, or Microsoft credentials into commands, manifests, or skill files.

## Editorial Standard

- Optimize for comprehension, not brevity alone: the artifact must work both after watching and instead of watching, with enough detail to reconstruct the complete argument and workflow.
- Use progressive disclosure on every page: plain-language point → mechanism/steps → implication → caveat.
- Keep bullets scannable: normally 12–28 words, one claim per bullet, with concrete nouns and verbs.
- Define acronyms and technical terms on first use; avoid unexplained shorthand.
- Remove biography, presenter commentary, channel promotion, engagement numbers, sponsor copy, and “the speaker says” phrasing.
- Make titles topic-based and self-contained. A reader should understand the page without knowing who presented it.
- Put uncertainty next to the affected claim. Prefer “Demo result; not independently benchmarked” over attribution-heavy prose.
- Keep `why_it_matters` to one direct operational takeaway, ideally under 20 words.

## How to Run

```text
# YouTube or another yt-dlp-supported public URL
terminal(command="<venv-python> <skill-dir>/scripts/visual_notes.py prepare '<video-url>' --workdir '<run-dir>' --interval 8", timeout=600)

# Local or downloaded private recording; transcript is optional
terminal(command="<venv-python> <skill-dir>/scripts/visual_notes.py prepare '<recording.mp4>' --transcript '<transcript.vtt>' --source-url '<original-link>' --title '<meeting-title>' --workdir '<run-dir>' --interval 8", timeout=600)

terminal(command="<venv-python> <skill-dir>/scripts/visual_notes.py build '<run-dir>/manifest.json' --output '<run-dir>/speaker-notes.pdf' --zip '<run-dir>/selected-frames.zip'", timeout=300)
```

`prepare` accepts a local video file, a video URL, or a YouTube channel URL. Channel URLs resolve to the latest upload. For remote public sources it downloads the video and attempts English subtitles. For local recordings it keeps the source in place, optionally copies the supplied transcript into the run directory, probes duration with `ffprobe`, extracts timestamped candidates, creates contact sheets, and writes `manifest.template.json`.

## Manifest

Copy `templates/manifest.example.json` to the run directory and fill it with one item per unique substantive visual. `slides` may contain any positive number of items. Each item supports:

- `timestamp`: seconds, `MM:SS`, or `HH:MM:SS`
- `title` and optional `subtitle`
- `image`: absolute path or path relative to the manifest
- optional `crop`: `[x1,y1,x2,y2]` in source-image pixels
- optional `layout`: `standard` or `wide`
- `notes`: detailed, plain-language notes that preserve the full conceptual thread
- `why_it_matters`: one concise core takeaway; the builder renders this as `CORE IDEA`, not “Why it matters” or “Important to note”

## Procedure

1. **Acquire private sources safely.** For an authenticated SharePoint/OneDrive link, open it in the user's logged-in browser and download the recording plus transcript when offered. If access is unavailable, ask the user to attach or download the files; do not attempt credential or cookie extraction. Completion criterion: a readable local video exists and its original private URL is retained only as metadata when appropriate.
2. **Prepare the run.** Use a unique directory under the Hermes scratch/cache area, create or reuse an isolated venv, verify imports and `ffmpeg`/`ffprobe`, then run `prepare`. Completion criterion: metadata, the accessible video source, transcript when available, timestamped candidate frames, contact sheets, and a manifest template exist.
3. **Read the transcript.** Use the supplied transcript, extracted subtitles, or transcribe the audio with an available speech-to-text tool. Build a topic outline before selecting frames. For meetings, include decisions, action items, owners, dates, unresolved questions, and risks only when supported by the recording. Completion criterion: every major argument, decision, data set, workflow, recommendation, and architecture concept is identified.
4. **Review every contact sheet.** Use `vision_analyze` on all sheets. Select every unique substantive visual; omit repeated animation builds, title cards without content, presenter-only shots, memes, sponsor/promotional filler, and redundant slides. Never target a predetermined count.
5. **Refine screenshots.** For selected timestamps, extract a nearby full-resolution frame with `ffmpeg`. Use `vision_analyze` to obtain exact crop coordinates that preserve all meaningful labels while removing presenter panels and broadcast chrome. Completion criterion: each selected visual is complete and readable.
6. **Write the manifest.** Order items by timestamp. Write detailed notes in plain language: one idea per bullet, short sentences, concrete steps/examples, and a brief definition the first time specialized jargon appears. Each page should explain **what the visual shows**, **how the concept or workflow works**, **why it matters**, and **the main caveat or limit**. Prefer 3–5 concise bullets over dense paragraphs. Do not mention the presenter, speaker, channel, biography, promotional framing, or narration process; describe the subject directly. Do not write phrases such as “the speaker says,” “the presenter explains,” or “in this video.” Distinguish claims from verified facts without attribution filler—for example, “Demo result; not independently benchmarked.” Preserve uncertainty and note commercial interests or benchmark limits only when they materially affect interpretation. Use `wide` only for genuinely wide diagrams; otherwise use `standard`.
7. **Build deliverables.** Run `build` with both `--output` and `--zip`. Completion criterion: PDF page count equals one cover plus one page per manifest item, and the ZIP contains every selected frame plus `index.csv`.
8. **Visual QA.** Render every PDF page to PNG with the `pdf` skill, inspect all pages with `vision_analyze`, and fix unreadable diagrams, clipping, overlaps, or weak crops. Dense visuals may justify a separate interpretation page; adding such pages is content-driven, not quota-driven.
9. **Deliver in messaging.** Return the PDF and ZIP as file attachments. On Telegram, a pasted YouTube URL is sufficient; do not ask the user to repeat the workflow request.

## Optional Archive

Archive outputs only when the current profile or user explicitly provides an archive repository. Resolve its location from the current machine or profile; never assume a machine-local path. Create one descriptive kebab-case folder per public video, update the library index without duplicates, commit, push, and verify the exact remote paths.

Never publish private meeting recordings, transcripts, screenshots, source links, or derived notes to a public repository. SharePoint, Teams, Zoom, OneDrive, and local-file sources are private by default unless the user explicitly confirms publication rights and requests publishing.

## OneNote Delivery

When OneNote storage is requested, create a structured Markdown companion beside the PDF and ZIP, then create or update the OneNote page only through authenticated Microsoft access. Verify the exact notebook/section/page by reading it back before claiming sync. If authentication is unavailable or declined, keep the OneNote-ready local artifact, report synchronization as pending, and never imply that local or OneDrive storage is the same as a OneNote page.

## Telegram Behavior

When this skill is installed in the same profile used by the Telegram gateway, the agent can execute it with full tool access. A per-chat Telegram `system_prompt` override may make the trigger deterministic: when a message contains a YouTube video or channel URL, run this skill automatically and send the resulting PDF and selected-frame ZIP back to the same chat. Keep Telegram allowlisting or DM pairing enabled because the workflow can use terminal tools.

## Pitfalls

- A SharePoint page URL is usually not a direct media URL. Download through the authenticated browser first; do not pass session cookies or tokens to `yt-dlp`.
- Local recordings may have no transcript. Use an available speech-to-text tool before drafting content-complete notes.
- Fixed candidate intervals can miss a brief slide. Use transcript timestamps and nearby frame extraction to recover it.
- Broadcast split-screen layouts need manual crops; do not stretch or recreate source screenshots unless the user asks.
- A slide animation may need only its final complete build. Keep earlier builds only when they carry distinct evidence.
- YouTube metadata and engagement counts are time-sensitive.
- A benchmark slide supports what the speaker reports, not a universal claim about every model or repository.
- `wide` layouts reduce image height and leave only a shallow notes panel; with the current builder, several bullets can be hidden behind the fixed-height CORE IDEA box. Prefer `standard` for multi-bullet notes, or shorten the notes and verify the rendered page visually.

## Verification

- Run `pytest scripts/test_visual_notes.py -q`; all tests must pass.
- `pdf_read.py --meta` reports the expected page count and no scanned pages.
- Extracted PDF text contains every manifest title.
- Every selected screenshot appears in the ZIP and `index.csv`.
- Visual inspection finds no accidental clipping, overlap, or unreadable essential labels.