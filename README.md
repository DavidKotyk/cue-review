# Cue Review

A local SRT review studio for freelance video editors. Diagnose rushed captions, ask an existing local Phi-3 model for tighter wording, approve individual changes, and export SRT plus a review audit. Timing and source text remain intact.

## Run

Python 3.10+ and an existing local Ollama installation with `phi3:latest` are required for suggestions. The web app uses only Python's standard library, browser JavaScript and local CSS. No package installation, credentials or cloud account is required. No automatic model downloads.

```sh
python3 server.py
```

Open **http://127.0.0.1:4190**. Import a plain-text English SRT, or choose **Try the studio sample**. The default database is `data/reviews.sqlite3`. To use an isolated database or another port:

```sh
python3 server.py --port 4191 --db /tmp/cue-review-demo.sqlite3
```

An existing Ollama server must listen on `127.0.0.1:11434`. Verify the installed model using `ollama list`; start Ollama normally if it is stopped. If `phi3:latest` is absent, inference fails with an explanatory error. This project does not install or pull weights. Import, diagnosis and export work without inference.

## Review workflow

1. Select a reading-speed profile and protected names before importing. These settings are copied into that review; changing the import controls applies to the next import.
2. Inspect reading speed, line length/count, short duration and overlap warnings. Defaults are 20 characters/second, 42 characters/line, 2 lines and 1-second minimum. They are house-style targets, not a standard or accessibility certification.
3. Click **Suggest a tighter cut** on a cue. Only that cue and its protected-term list go to the local model. Generation can take up to 90 seconds.
4. Check the draft against the actual audio, edit if necessary, then approve or reject it. Numbers and protected terms are conservatively checked. These checks do **not** prove that meaning, units, negation or speaker intent survived.
5. Export two files: reviewed SRT and JSON audit. Your browser may ask to permit both downloads. Pending/rejected drafts do not replace source text. Remaining warnings are recorded; unresolved timing is never silently repaired.

Reopening the app resumes the last review ID stored by that browser. The database survives server restarts. There is no review library UI; keep your exports. Restore original is reversible. Caption text, model prompts and decisions are stored unencrypted locally. Keep private client data out of published demos and audit files.

## Verify

```sh
python3 -m unittest discover -s tests -v
python3 tests/model_check.py
```

The first command runs eleven domain and actual HTTP tests without a model. The second performs four **actual local** Phi-3 calls on fictional text and overwrites `evidence/model-check.json`. It is a small smoke evaluation, not a production benchmark. Recorded results include two semantic weaknesses even though structural guards passed. See [evidence/TEST-REPORT.md](evidence/TEST-REPORT.md).

The included walkthrough is assembled from screenshots of the real app, not a continuous screen recording. See [demo/WALKTHROUGH.md](demo/WALKTHROUGH.md), `demo/walkthrough.mp4`, input `demo/studio-demo.srt`, reviewed output and audit.

## Boundaries

- English plain-text SRT only; no caption markup, positioning extensions, audio transcription, translation, video playback or forced alignment.
- Up to 500 cues / 250 KB. Cue timestamps/order and indices are preserved; overlap and duration repairs belong in a video editor.
- A suggestion may shorten incorrectly or fail to satisfy the reading-speed target. Editor review remains essential. Synthetic sample approvals were performed by the AI-assisted test operator, not an independent customer.
- Single-user loopback prototype, without accounts or authentication. Do not expose the server or database to a network. Host, Origin and cross-site request checks reduce browser-origin misuse; they are not a boundary against other processes on the same computer.
- Not tested on client projects, with professional caption editors, or for measured time savings. Willingness to pay is an unvalidated hypothesis.

## Provenance and event status

New project created October 16, 2026 for DEV Hacktoberfest Week 2: Side Hustle. Source, interface, fictional fixtures, tests, entry draft and media assembly were produced with Codex assistance under David Kotyk's direction. No source from What Changed?, Submission Desk, Pantry Before Shopping or the GitLab project was reused. Open-source runtime/model components are credited in [THIRD-PARTY.md](THIRD-PARTY.md).

This is a **local entry candidate**. No public source, public demo or DEV submission has been published. The overall award is competitive USD 250, not payment for completion. The payout method remains unconfirmed. A separate local review packet records the exact deadline, conditions and remaining approvals; personal review records are excluded from the public source inventory. Any commits after October 18, 2026 at 11:59 p.m. PDT must be noted here before entry.
