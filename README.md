# 1:1 Synchronized Free AI YouTube Shorts Generator

A 100% free, local-first engine that renders vertical shorts (1080x1920) with frame-accurate word-level visual synchronization, neural voiceover, and kinetic karaoke subtitles.

## Key Features

1. **Audio as Master Clock**: Uses `faster-whisper` word-level timestamps (`timeline.json`) to anchor all cuts, zooms, and animations.
2. **Micro-Shot Planning**: Breaks narration into 5-9 word micro-shots (~2-3 seconds each). No visual stays longer than 3.5s without dynamic change.
3. **1:1 Visual Match**: Generates literal physical prompts from narration keywords.
4. **Multi-Tier Visual Engine**:
   - Tier 1: Pollinations AI (High-res 9:16 vertical images)
   - Tier 2: Unsplash local photo fallback
   - Tier 3: Sleek gradient kinetic keyword cards
   - Deterministic cache by hash(`prompt + seed`)
5. **Match Verification**: Scans every visual against narration keywords and logs audit scores.
6. **Karaoke Subtitles**: ASS word-by-word highlight pops synced to the exact audio master clock.
7. **Post-Render Sync Report**: Outputs a table showing shot id, narration, duration, key words, and alignment scores.

## Architecture & Files

- `config.yaml` - Master configuration (resolutions, FPS, Whisper snapshot, timing thresholds)
- `backend/timeline_engine.py` - Audio master clock generation via faster-whisper
- `backend/shot_planner.py` - Micro-shot chunking & concrete visual prompt mapping
- `backend/visual_engine.py` - Free multi-tier generation, caching, and match verification
- `backend/subtitle_generator.py` - ASS word-by-word pop karaoke styling
- `backend/video_renderer.py` - Ken Burns camera motions, audio ducking, subtitle burning
- `backend/sync_report.py` - Sync auditing table and warning logger
- `backend/app.py` - FastAPI server with REST endpoints & background task pipeline
- `static/index.html` & `static/app.js` - Web UI with speed controls and visual preview

## How to Run

1. Start the server:
   ```powershell
   python -m uvicorn app:app --app-dir "backend" --host 127.0.0.1 --port 8000 --reload
   ```
2. Open your browser:
   ```
   http://127.0.0.1:8000
   ```
3. Run tests:
   ```powershell
   $env:PYTHONPATH="."; python -m pytest tests/test_sync_engine.py -v
   ```
