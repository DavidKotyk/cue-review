# Verification report — October 16, 2026

## Domain and HTTP

Eleven tests passed in the recorded final run: `unit-tests.txt`. Tests cover BOM/CRLF parsing and exact-time roundtrip; malformed/duplicate/empty/out-of-order captions; overlap and readability diagnostics; proposal-versus-approved export; rejection, restoration and persistence; stale revisions; model failure without mutation; a model returning after another edit; altered numbers/protected terms/markup; invalid profiles; and real HTTP import/get/export with Host, Origin, cross-site and stale-request checks.

The store adapter is stubbed in domain tests so failure/race scenarios are reproducible. Those tests do not establish model quality. Actual model calls and the real browser server path are separate below.

## Actual local inference

Four fictional cases called the existing `phi3:latest` model through local Ollama. See `model-check.json` for exact prompts, text, elapsed times and response tokens. Recorded calls took 2.071–3.998 seconds on this Mac. These are four observations, not a latency guarantee or benchmark average.

1. Verbose Solara instruction became “Press Solara's green button to start.” Core action and protected term retained in this fixture.
2. Power-off instruction retained negation and the “until” condition.
3. “Wait 10 seconds before you open it” became “Wait 10s.” It retained the numeric token but removed the opening condition. This **failed semantic review** and was rejected in the browser demo.
4. A studio opening/closing sentence became an ambiguous time range. Numeric/name guards passed; semantic quality remains insufficient.

All four passed structural guards. Two have documented semantic concerns. No real-world accuracy percentage, paid-user result or professional validation claimed.

## Actual browser workflow

Tested local server at 127.0.0.1:4190 in the Codex in-app browser, using real HTTP and Ollama, not a simulated model response.

- Loaded sample: five cues, three initially flagged.
- Filtered to flagged cues.
- Generated cue 2 draft using local model; pending count became one, approved count stayed zero.
- Downloaded SRT before approval; file matched original sample. Copy: `browser-unapproved-export.srt`.
- Approved cue 2: reading-speed estimate changed from 24.29 to 10.57 chars/s; remaining flagged cues changed from three to two.
- Generated cue 4's “Wait 10s,” then rejected it for semantic loss. Its original text remained in exported SRT.
- Browser reload after an actual server restart restored the persisted review and pending draft.
- Dropping protected term Solara in an editable draft produced “Suggestion changed protected term: Solara.” Approved earlier text remained intact. Rejected the test draft afterward.
- Uploaded actual `tests/invalid.srt` through the file picker. UI rejected reversed timestamps and preserved the prior review.
- Exported reviewed SRT. Re-parsed output: five cues, all original timestamps, only the approved cue replaced. Evidence: `export-check.json`, `demo/reviewed.srt` and `demo/review-audit.json`.
- Desktop 1280×900 and mobile 390×844 inspected. Mobile DOM scroll width equaled viewport width (390); no horizontal overflow observed. Screenshots in `demo/`.
- Browser console warning/error query returned an empty list during verification.

Synthetic decisions were performed by the AI-assisted test operator. No independent human caption-editor validation, audio comparison, accessibility certification, load test or hostile-local-process security audit was performed.
