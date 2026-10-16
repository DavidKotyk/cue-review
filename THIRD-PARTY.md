# Third-party components and disclosures

The application itself has no third-party Python/JavaScript runtime packages. Python/SQLite and browser APIs provide storage and UI. No fonts, image libraries or external scripts load in the app.

- **Ollama**: existing local model-serving software, MIT-licensed open-source runtime. https://github.com/ollama/ollama . No Ollama code or model weights copied into this repository. HTTP calls are restricted in code to the existing local endpoint; no account or paid API.
- **Phi-3 mini** through existing `phi3:latest`: Microsoft open-weight model. Official model card identifies an MIT license: https://huggingface.co/microsoft/Phi-3-mini-4k-instruct . Local manifest/runtime details are recorded in `evidence/local-runtime.json`. This project does not redistribute weights, fine-tune a model or claim model authorship. A mutable Ollama tag is not proof of an upstream training checkpoint; local manifest digest is recorded for reproducibility.
- **Codex**: AI-assisted implementation, test execution, visual review, writing and screenshot/video preparation. The runtime caption suggestions use local Phi-3; Codex is the development assistant. No claim of unaided human authorship.
- **Demo assembly only**: Pillow, NumPy and imageio-ffmpeg from the existing local Python environment; ffmpeg encodes real screenshots plus explanatory text into the walkthrough. These are not dependencies for running the app. Screenshots depict fictional captions. No third-party photos, video, music, logos or client data used.

App name is an independent working title. No Microsoft, Ollama, MLH or DEV sponsorship/endorsement claimed.
