# AI Shorts Studio — 1:1 Visual Match Engine

<div align="center">

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)
![Free](https://img.shields.io/badge/cost-100%25%20Free-brightgreen.svg)
![No API Key](https://img.shields.io/badge/API%20Key-Not%20Required-success.svg)

**A fully local, 100% free AI pipeline that renders YouTube Shorts / TikToks / Reels with frame-accurate word-level visual synchronization, neural voiceover, and animated karaoke subtitles.**

[Features](#-features) · [Architecture](#-architecture) · [Quick Start](#-quick-start) · [Configuration](#-configuration) · [API Reference](#-api-reference) · [Contributing](#-contributing)

</div>

---

## ✨ Features

| Feature | Detail |
|---------|--------|
| 🎙️ **Neural Voiceover** | Microsoft Edge-TTS — 40+ free voices across Hindi, English (US/UK/AU) |
| ⏱️ **Word-Level Sync** | `faster-whisper` extracts millisecond-precise word timestamps |
| 🎬 **Micro-Shot Planning** | Narration split into 5–9 word micro-shots (~2–3 s each); visuals never repeat |
| 🖼️ **Multi-Tier Visuals** | Pollinations AI → Unsplash → Procedural Gradient (all free, no key needed) |
| 🔍 **Unique Visual Check** | Per-shot cache key (prompt + seed + shot_id) + duplicate-hash retry logic |
| 📝 **Karaoke Subtitles** | ASS word-by-word highlight pops, 4 style presets |
| 📊 **Sync Report** | Post-render table: shot id · narration · duration · keywords · alignment score |
| 🎵 **Background Music** | Auto-ducked ambient music layer |
| 🖥️ **Web UI** | Dark-mode Tailwind UI — no frontend build step required |
| 🔌 **REST API** | Full FastAPI backend; scriptable from any client |

---

## 🏗️ Architecture

```
AI-SHORTS-VIDEO/
├── backend/
│   ├── app.py               # FastAPI server & render pipeline
│   ├── config.py            # Path constants & UI presets
│   ├── script_engine.py     # Script parsing & scene extraction
│   ├── tts_engine.py        # Edge-TTS neural voiceover
│   ├── timeline_engine.py   # faster-whisper word-timestamp master clock
│   ├── shot_planner.py      # Micro-shot chunking & visual prompt mapping
│   ├── visual_engine.py     # Free multi-tier image generation & caching
│   ├── subtitle_generator.py# ASS karaoke subtitle generation
│   ├── video_renderer.py    # Ken Burns clips, audio ducking, FFmpeg assembly
│   └── sync_report.py       # Post-render audit table
├── static/
│   ├── index.html           # Web UI (Tailwind CDN, no build step)
│   ├── app.js               # Frontend logic
│   └── style.css            # Custom animations & overrides
├── assets/
│   └── music/               # Background music tracks (drop .mp3 files here)
├── tests/
│   └── test_sync_engine.py  # Sync pipeline tests
├── config.yaml              # Master configuration
├── requirements.txt         # Python dependencies
└── run.bat                  # One-click Windows launcher
```

### Render Pipeline

```
Script Input
    │
    ▼
[1] Edge-TTS Voiceover  ──────────────────────► master_speech.mp3
    │
    ▼
[2] faster-whisper Word Timestamps  ──────────► timeline.json
    │
    ▼
[3] Micro-Shot Planner (5-9 words/shot)  ─────► shots[]
    │
    ▼
[4] Visual Engine (per shot)
    ├─ Tier 1: Pollinations AI (free, no key)
    ├─ Tier 2: Unsplash stock fallback
    └─ Tier 3: Procedural gradient card
    │
    ▼
[5] Ken Burns Clip Renderer  ────────────────► shot_XX.mp4 × N
    │
    ▼
[6] ASS Karaoke Subtitles  ──────────────────► subtitles.ass
    │
    ▼
[7] FFmpeg Final Assembly  ──────────────────► final_short.mp4
    │
    ▼
[8] Sync Report  ────────────────────────────► sync_report.json
```

---

## 🚀 Quick Start

### Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.10+ |
| FFmpeg | Any recent version (auto-bundled via `imageio-ffmpeg`) |
| Ollama (optional) | For LLM-assisted shot planning (`qwen2.5:1.5b`) |

> **Note:** Ollama is **optional**. The shot planner falls back to a deterministic rule-based splitter automatically if Ollama is not running.

### 1. Clone the repository

```bash
git clone https://github.com/divyarajsingh2021-pixel/AI-SHORTS-VIDEO.git
cd AI-SHORTS-VIDEO
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the server

**Windows (easiest):**
```bat
run.bat
```

**Cross-platform:**
```bash
python -m uvicorn app:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

### 4. Open the Web UI

```
http://127.0.0.1:8000
```

---

## ⚙️ Configuration

All settings live in [`config.yaml`](config.yaml). The important ones:

```yaml
whisper:
  # "tiny" downloads the model automatically (~75 MB, runs on CPU).
  # For better accuracy use "base" or "small".
  model_snapshot: "tiny"
  device: "cpu"
  compute_type: "int8"

micro_shots:
  ollama_model: "qwen2.5:1.5b"       # Ollama model for shot planning (optional)
  ollama_url: "http://127.0.0.1:11434"
  fallback_to_rules: true             # Always true — never crashes without Ollama

visuals:
  engine_primary: "pollinations"      # Free, no key required
  engine_fallback: "unsplash"
  engine_last_resort: "gradient_card"
```

### Visual Engines

| Tier | Engine | Notes |
|------|--------|-------|
| 1 | **Pollinations AI** | Free, high-resolution 9:16 AI images, no account needed |
| 2 | **Unsplash** | Free stock photos via public source URL |
| 3 | **Gradient Card** | Procedural kinetic cards generated locally — always works offline |

---

## 📡 API Reference

All endpoints are served by the FastAPI backend at `http://127.0.0.1:8000`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/status` | Health check |
| `GET` | `/api/voices` | List available TTS voices |
| `GET` | `/api/visual-styles` | List art style presets |
| `GET` | `/api/subtitle-styles` | List subtitle style presets |
| `GET` | `/api/voice-speeds` | List playback speed options |
| `POST` | `/api/parse-script` | Parse raw script into scenes |
| `POST` | `/api/preview-visuals` | Generate preview images for scenes |
| `POST` | `/api/regenerate-scene-visual` | Regenerate the visual for one scene |
| `POST` | `/api/render-short` | Start the full render pipeline |
| `GET` | `/api/render-status/{session_id}` | Poll render progress |
| `GET` | `/api/output/{session_id}/{filename}` | Download output files |

**Interactive Swagger docs:** `http://127.0.0.1:8000/docs`

---

## 🧪 Running Tests

```bash
# From the project root
python -m pytest tests/test_sync_engine.py -v
```

---

## 🔒 Security Notes

- **No API keys required or stored.** All visual generation uses free, public endpoints.
- The server binds to `127.0.0.1` (localhost only) by default — it is **not exposed** to the network.
- The `CORS` middleware is set to `allow_origins=["*"]` for local development convenience. If you expose this server publicly, restrict the allowed origins.
- Output files are served from a session-scoped directory; sessions are identified by a UUID.

---

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/my-feature`.
3. Commit your changes: `git commit -m "feat: add my feature"`.
4. Push and open a Pull Request.

Please keep PRs focused and include a brief description of the change.

---

## 📄 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

<div align="center">

Made with ❤️ · Powered by Edge-TTS · faster-whisper · Pollinations AI · FFmpeg

</div>
