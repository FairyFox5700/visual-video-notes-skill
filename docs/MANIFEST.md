# Manifest reference

The manifest controls the PDF structure, selected images, crops, notes, and core ideas. `prepare` writes `manifest.template.json`; copy it to `manifest.json` and fill the `slides` array.

## Top-level fields

| Field | Required | Description |
|---|---:|---|
| `report_title` | Yes | Title shown on the cover |
| `video_title` | Yes | Source video or meeting title |
| `source_url` | Yes | Original URL or a local file URI; appears in the footer |
| `duration` | No | Display text such as `42:18` or `1:08:04` |
| `author` | No | PDF metadata author; defaults to `Hermes Agent` |
| `selection_policy` | No | Editorial note describing what was included or excluded |
| `slides` | Yes | Non-empty array of selected visual-note items |

Additional descriptive fields are allowed but are not rendered by the current builder.

## Slide fields

| Field | Required | Description |
|---|---:|---|
| `timestamp` | Yes | Seconds, `MM:SS`, or `HH:MM:SS`; decimals are accepted |
| `title` | Yes | Self-contained topic title |
| `subtitle` | No | Short framing line |
| `image` | Yes | Absolute path or path relative to the manifest |
| `crop` | No | `[x1, y1, x2, y2]` in source-image pixels |
| `layout` | No | `standard` or `wide`; defaults to `standard` |
| `notes` | Yes | Non-empty list of concise explanatory bullets |
| `why_it_matters` | Yes | One direct core takeaway |

## Complete presentation example

```json
{
  "report_title": "Visual Notes — Reliable agent workflows",
  "video_title": "Reliable agent workflows",
  "source_url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "duration": "38:42",
  "slides": [
    {
      "timestamp": "04:18",
      "title": "The orchestration loop separates planning from execution",
      "subtitle": "Tools return evidence before the next decision",
      "image": "candidates/frame_00033_000256.jpg",
      "crop": [80, 40, 1200, 680],
      "layout": "standard",
      "notes": [
        "The planner selects one bounded action instead of generating an entire workflow in advance.",
        "Each tool result becomes evidence for the next decision, reducing unsupported assumptions.",
        "Retries need explicit limits so transient failures do not become endless loops."
      ],
      "why_it_matters": "Evidence-driven loops make failures observable and recovery controllable."
    }
  ]
}
```

## Complete meeting example

```json
{
  "report_title": "Architecture review — checkout modernization",
  "video_title": "Checkout modernization review",
  "source_url": "https://contoso.sharepoint.com/:v:/r/sites/team/...",
  "duration": "52:10",
  "slides": [
    {
      "timestamp": "18:42",
      "title": "Payment orchestration remains behind the existing API",
      "subtitle": "Decision recorded during architecture review",
      "image": "candidates/frame_00142_001128.jpg",
      "layout": "wide",
      "notes": [
        "The public checkout API remains stable while payment providers move behind an orchestration service.",
        "The team chose incremental migration to avoid changing web and mobile clients simultaneously.",
        "Action: Maya will document timeout and retry behavior before the next design review.",
        "Open question: the recording does not establish who owns provider-level reconciliation."
      ],
      "why_it_matters": "A stable boundary reduces migration risk but requires explicit failure semantics."
    }
  ]
}
```

## Timestamp rules

Accepted:

```text
75
"75.5"
"01:15"
"1:01:15.5"
```

Rejected:

```text
"1:99"
"one minute"
-5
```

## Crop guidance

A crop uses source-image pixels:

```json
"crop": [100, 50, 1180, 650]
```

This means left `100`, top `50`, right `1180`, bottom `650`. The right edge must be greater than the left edge, and the bottom edge must be greater than the top edge.

Keep all meaningful labels, legends, axes, and callouts. Remove presenter panels or broadcast chrome only when they are not informational.

## Layout guidance

### `standard`

Use for most slides. It places the image on the left and a tall notes panel on the right. This is the safer option for three to five bullets.

### `wide`

Use for genuinely wide diagrams or dense dashboards. The notes area is shallow, so shorten the notes and inspect the rendered page carefully.

## Writing guidance

- Use one claim per bullet.
- Explain what the visual shows, how it works, why it matters, and the main limit.
- Define specialized terms on first use.
- State decisions directly rather than writing “the speaker says.”
- Label uncertainty where it matters.
- Do not invent meeting owners, deadlines, decisions, or benchmark conclusions.
