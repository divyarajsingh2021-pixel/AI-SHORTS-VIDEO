import os
import uuid
import json
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import (
    BASE_DIR, BACKEND_DIR, STATIC_DIR, OUTPUT_DIR, ASSETS_DIR, MUSIC_DIR,
    POPULAR_VOICES, SUBTITLE_STYLES, VOICE_SPEEDS, VISUAL_STYLES
)
from script_engine import ScriptEngine
from tts_engine import TTSEngine
from timeline_engine import build_audio_timeline, save_timeline
from shot_planner import plan_micro_shots, MicroShot
from visual_engine import generate_shot_visual, verify_visual_match, clear_session_hashes
from subtitle_generator import SubtitleGenerator
from video_renderer import VideoRenderer
from sync_report import generate_sync_report

app = FastAPI(title="Free Custom AI Shorts Generator with 1:1 Visual Match")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active rendering status tracker
RENDER_STATUS: Dict[str, Any] = {}

class ParseScriptRequest(BaseModel):
    raw_script: str
    visual_style: Optional[str] = "cinematic"
    topic_context: Optional[str] = ""

class GenerateScenesRequest(BaseModel):
    scenes: List[Dict[str, Any]]
    voice: str = "hi-IN-MadhurNeural"
    voice_speed: str = "+15%"
    visual_style: str = "cinematic"
    subtitle_style: str = "hormozi"
    layout_mode: str = "fullscreen"
    music_track: Optional[str] = "ambient_chill"
    preview_mode: bool = False

class PreviewVisualsRequest(BaseModel):
    scenes: List[Dict[str, Any]]
    session_id: Optional[str] = None

class RegenerateVisualRequest(BaseModel):
    scene_id: int
    prompt: str
    session_id: str
    motion: str = "zoom_in"
    duration: float = 3.0

@app.get("/api/status")
def get_status():
    return {"status": "ok", "message": "1:1 Visual Match AI Shorts Engine Online"}

@app.get("/api/voices")
def get_voices():
    return POPULAR_VOICES

@app.get("/api/presets")
def get_presets():
    return ScriptEngine.get_presets()

@app.get("/api/preset/{key}")
def get_preset_detail(key: str):
    return ScriptEngine.get_preset_data(key)

@app.get("/api/subtitle-styles")
def get_subtitle_styles():
    return {k: {"name": v["name"], "font": v["font"]} for k, v in SUBTITLE_STYLES.items()}

@app.get("/api/voice-speeds")
def get_voice_speeds():
    return VOICE_SPEEDS

@app.get("/api/visual-styles")
def get_visual_styles():
    return VISUAL_STYLES

@app.post("/api/parse-script")
def parse_script(req: ParseScriptRequest):
    scenes = ScriptEngine.parse_custom_script(
        raw_text=req.raw_script,
        visual_style=req.visual_style or "cinematic",
        topic_context=req.topic_context or ""
    )
    return {"scenes": scenes, "total_scenes": len(scenes)}

@app.post("/api/preview-visuals")
def preview_visuals(req: PreviewVisualsRequest):
    session_id = req.session_id or f"preview_{uuid.uuid4().hex[:8]}"
    session_dir = OUTPUT_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for i, sc in enumerate(req.scenes):
        idx = i + 1
        img_path = session_dir / f"scene_{idx:02d}.jpg"
        if not img_path.exists():
            if i > 0:
                time.sleep(0.8)
            generate_shot_visual(
                prompt=sc["visual_prompt"],
                output_path=str(img_path),
                seed=42 + idx,
                width=540,
                height=960,
                keywords=sc.get("keywords", []),
                shot_id=idx
            )
        results.append({
            "scene_id": idx,
            "image_url": f"/api/output/{session_id}/scene_{idx:02d}.jpg",
            "prompt": sc["visual_prompt"]
        })
    return {"session_id": session_id, "visuals": results}

@app.post("/api/regenerate-scene-visual")
def regenerate_scene_visual(req: RegenerateVisualRequest):
    session_dir = OUTPUT_DIR / req.session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    img_path = session_dir / f"scene_{req.scene_id:02d}.jpg"
    if img_path.exists():
        try:
            img_path.unlink()
        except Exception:
            pass

    new_seed = int(uuid.uuid4().int % 100000)
    generate_shot_visual(
        prompt=req.prompt,
        output_path=str(img_path),
        seed=new_seed,
        width=540,
        height=960,
        shot_id=req.scene_id
    )

    return {
        "status": "success",
        "scene_id": req.scene_id,
        "image_url": f"/api/output/{req.session_id}/scene_{req.scene_id:02d}.jpg?t={new_seed}"
    }

async def render_pipeline(session_id: str, req: GenerateScenesRequest):
    session_dir = OUTPUT_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    clear_session_hashes()
    RENDER_STATUS[session_id] = {"status": "processing", "progress": 5, "message": "Synthesizing voiceover (audio master clock)..."}

    try:
        # STEP 1: Generate Master Voiceover & Word Timeline
        tts_result = await TTSEngine.process_scenes(req.scenes, req.voice, session_dir, voice_speed=req.voice_speed)
        processed_scenes = tts_result["scenes"]
        total_duration = tts_result["total_duration"]

        master_audio = session_dir / "master_speech.mp3"
        scene_audios = [Path(s["audio_file"]) for s in processed_scenes]
        VideoRenderer.concatenate_audio_tracks(scene_audios, master_audio)

        full_text = " ".join(s["text"] for s in processed_scenes)
        RENDER_STATUS[session_id] = {
            "status": "processing",
            "progress": 20,
            "message": "Extracting faster-whisper word timestamps (audio master clock)..."
        }

        timeline = build_audio_timeline(str(master_audio), reference_text=full_text)
        timeline_path = session_dir / "timeline.json"
        save_timeline(timeline, str(timeline_path))

        # STEP 2: Micro-Shot Planning (5-9 words per shot for 1:1 visual match)
        RENDER_STATUS[session_id] = {
            "status": "processing",
            "progress": 35,
            "message": "Planning 1:1 micro-shots & concrete visual ideas..."
        }
        shots = plan_micro_shots(timeline, art_style=req.visual_style, scenes=processed_scenes)

        # STEP 3 & 4: Free Visual Generation & Match Verification
        RENDER_STATUS[session_id] = {
            "status": "processing",
            "progress": 45,
            "message": f"Generating {len(shots)} 1:1 matched visuals with match scoring..."
        }

        verification_results = []
        shot_clips = []
        video_w = 540 if req.preview_mode else 1080
        video_h = 960 if req.preview_mode else 1920

        for s in shots:
            idx = s.shot_id + 1
            img_path = session_dir / f"shot_{idx:02d}.jpg"
            clip_path = session_dir / f"shot_{idx:02d}.mp4"
            dur = max(0.5, s.end_time - s.start_time)

            if not img_path.exists():
                generate_shot_visual(
                    prompt=s.visual_prompt,
                    output_path=str(img_path),
                    seed=42 + idx,
                    width=540,
                    height=960,
                    keywords=s.keywords,
                    shot_id=idx
                )

            # Match verification & scoring
            score, hits = verify_visual_match(str(img_path), s.narration_text, s.keywords)
            verification_results.append({"shot_id": s.shot_id, "score": score, "hits": hits})

            # Render Ken Burns motion clip
            VideoRenderer.render_micro_shot_clip(
                image_path=img_path,
                duration=dur,
                output_clip_path=clip_path,
                camera_motion=s.camera_motion,
                width=video_w,
                height=video_h
            )
            shot_clips.append(clip_path)

            pct = 45 + int((idx / len(shots)) * 30)
            RENDER_STATUS[session_id] = {
                "status": "processing",
                "progress": pct,
                "message": f"Synced micro-shot {idx}/{len(shots)} to spoken word: '{s.key_word}'"
            }

        # STEP 5: Burn Subtitles from timeline.json & assemble
        RENDER_STATUS[session_id] = {
            "status": "processing",
            "progress": 80,
            "message": "Generating Karaoke Subtitles from master timeline..."
        }

        ass_path = session_dir / "subtitles.ass"
        SubtitleGenerator.create_ass_subtitles_from_timeline(timeline, ass_path, req.subtitle_style)

        master_video = session_dir / "master_visual.mp4"
        VideoRenderer.concatenate_scene_clips(shot_clips, master_video)

        # Background music
        bgm_path = None
        if req.music_track:
            candidate_bgm = MUSIC_DIR / f"{req.music_track}.mp3"
            if candidate_bgm.exists():
                bgm_path = candidate_bgm

        RENDER_STATUS[session_id] = {
            "status": "processing",
            "progress": 90,
            "message": "Finalizing 1:1 synchronized Short with FFmpeg..."
        }

        final_video = session_dir / "final_short.mp4"
        VideoRenderer.assemble_final_short(
            video_track=master_video,
            audio_track=master_audio,
            ass_subtitles=ass_path,
            output_final_path=final_video,
            bgm_track=bgm_path,
            layout_mode=req.layout_mode,
            preview_mode=req.preview_mode
        )

        # STEP 6: Post-Render Sync Report Table
        sync_report_text = generate_sync_report(shots, verification_results, str(session_dir))
        try:
            safe_text = sync_report_text.encode('ascii', errors='backslashreplace').decode('ascii')
            print("\n" + "=" * 80)
            print("1:1 VISUAL SYNC REPORT:\n" + safe_text)
            print("=" * 80 + "\n")
        except Exception:
            pass

        RENDER_STATUS[session_id] = {
            "status": "completed",
            "progress": 100,
            "message": "Short Rendered Successfully with 1:1 Word Sync!",
            "video_url": f"/api/output/{session_id}/final_short.mp4",
            "sync_report_url": f"/api/output/{session_id}/sync_report.json"
        }

    except Exception as e:
        safe_err = str(e).encode('ascii', errors='backslashreplace').decode('ascii')
        print(f"[RenderPipeline] Failure in session {session_id}: {safe_err}")
        print(f"[RenderPipeline] Failure in session {session_id}: {e}")
        RENDER_STATUS[session_id] = {
            "status": "failed",
            "progress": 0,
            "message": f"Render failed: {str(e)}"
        }

@app.post("/api/render-short")
async def start_render(req: GenerateScenesRequest, background_tasks: BackgroundTasks):
    session_id = f"short_{uuid.uuid4().hex[:12]}"
    RENDER_STATUS[session_id] = {"status": "starting", "progress": 0, "message": "Initializing 1:1 render pipeline..."}
    background_tasks.add_task(render_pipeline, session_id, req)
    return {"session_id": session_id}

@app.get("/api/render-status/{session_id}")
def check_render_status(session_id: str):
    if session_id not in RENDER_STATUS:
        return {"status": "not_found", "message": "Session not found"}
    return RENDER_STATUS[session_id]

@app.get("/api/output/{session_id}/{filename}")
def serve_output_file(session_id: str, filename: str):
    file_path = OUTPUT_DIR / session_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Requested file not found")
    media_type = "video/mp4" if filename.endswith(".mp4") else ("image/jpeg" if filename.endswith(".jpg") else "application/json")
    return FileResponse(str(file_path), media_type=media_type)

# Mount static frontend
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
