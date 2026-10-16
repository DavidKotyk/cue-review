# Local demonstration

`walkthrough.mp4` is a 62-second silent walkthrough assembled from **actual browser screenshots**, with explanatory headings. It is not a continuous screen recording, a customer testimonial or proof of real-world caption accuracy. Input is original fictional studio text. The supplied SRT files are not audio-synchronized to this walkthrough.

1. Open the local studio and import `studio-demo.srt`, or use the sample button.
2. Cue 2 is verbose (24.29 characters/s). Click Suggest a tighter cut. Existing local Phi-3 proposes “Press Solara's green button to start.”
3. Inspect meaning and protected name, then approve. Cue 2 becomes 10.57 characters/s with the same timestamps. Both source and approved version remain visible.
4. Cue 4 is deliberately too short and overlapping. The model's “Wait 10s” omits the opening condition. Reject it; the original remains in `reviewed.srt` and timing warnings remain unresolved.
5. Export SRT and JSON audit. `review-audit.json` contains final-code actual proposals and decisions, including the rejected draft. Fictional decisions were made by the AI-assisted test operator, not an independent human editor.

The other screenshots document mobile rendering, protected-term validation and the real review UI. `01-open.jpg` is the initial narrow viewport; desktop and 390-pixel mobile layouts were checked separately.

Optional media rebuild with an environment that already has Pillow, NumPy and imageio-ffmpeg:

```sh
python3 demo/make_walkthrough.py
```

This optional script is not needed to run the app. No media or model download is performed.
