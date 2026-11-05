"""
Timeline Engine: Audio is the master clock.
Uses faster-whisper with word_timestamps=True on the final audio file
to produce a structured timeline.json where every single word has an exact
start and end timestamp.
"""

from typing import List, Dict, Any, Optional
import os
import json
import re
from pathlib import Path

# Try importing faster-whisper
try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

_WHISPER_INSTANCE: Optional[Any] = None

def get_whisper_model(snapshot_path: Optional[str] = None):
    global _WHISPER_INSTANCE
    if _WHISPER_INSTANCE is not None:
        return _WHISPER_INSTANCE

    if snapshot_path and os.path.exists(snapshot_path):
        _WHISPER_INSTANCE = WhisperModel(snapshot_path, device="cpu", compute_type="int8")
    else:
        # fallback default
        default_snap = r"C:\Users\hp\.cache\huggingface\hub\models--Systran--faster-whisper-tiny\snapshots\d90ca5fe260221311c53c58e660288d3deb8d356"
        if os.path.exists(default_snap):
            _WHISPER_INSTANCE = WhisperModel(default_snap, device="cpu", compute_type="int8")
        else:
            _WHISPER_INSTANCE = WhisperModel("tiny", device="cpu", compute_type="int8")
    return _WHISPER_INSTANCE


def build_audio_timeline(audio_path: str, reference_text: str = "", whisper_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Transcribes audio and aligns words to exact timestamps.
    Returns list of dicts:
    [
        {"word": "...", "start": 0.00, "end": 0.45, "index": 0},
        ...
    ]
    Handles Devanagari/Hindi scripts gracefully by matching Whisper timings to reference text words.
    """
    model = get_whisper_model(whisper_path)
    
    is_hindi = bool(re.search(r'[\u0900-\u097F]', reference_text))
    lang = "hi" if is_hindi else "en"
    
    # 1. Run Whisper transcription with word timestamps
    segments, info = model.transcribe(
        audio_path,
        language=lang,
        word_timestamps=True,
        vad_filter=True
    )
    
    whisper_words: List[Dict[str, Any]] = []
    for segment in segments:
        if hasattr(segment, 'words') and segment.words:
            for w in segment.words:
                whisper_words.append({
                    "word": w.word.strip(),
                    "start": round(float(w.start), 3),
                    "end": round(float(w.end), 3)
                })
        else:
            whisper_words.append({
                "word": segment.text.strip(),
                "start": round(float(segment.start), 3),
                "end": round(float(segment.end), 3)
            })

    # If reference text is provided and differs (e.g. Devanagari vs romanized whisper),
    # map exact timestamps onto original reference tokens
    if reference_text:
        ref_tokens = reference_text.strip().split()
        if ref_tokens and whisper_words:
            total_duration = whisper_words[-1]["end"] if whisper_words else 10.0
            first_start = whisper_words[0]["start"] if whisper_words else 0.0
            
            # If whisper tokens match in count roughly or if we need original script words:
            timeline = []
            num_ref = len(ref_tokens)
            num_whisp = len(whisper_words)
            
            if abs(num_ref - num_whisp) <= max(2, int(num_ref * 0.25)):
                # High correlation: interpolate or map directly
                for i, token in enumerate(ref_tokens):
                    whisp_idx = min(int(i * (num_whisp / num_ref)), num_whisp - 1)
                    w_item = whisper_words[whisp_idx]
                    timeline.append({
                        "word": token,
                        "start": w_item["start"],
                        "end": w_item["end"],
                        "index": i
                    })
            else:
                # Proportional distribution across the exact spoken bounds
                span = max(0.5, total_duration - first_start)
                step = span / num_ref
                for i, token in enumerate(ref_tokens):
                    w_start = round(first_start + i * step, 3)
                    w_end = round(first_start + (i + 1) * step, 3)
                    timeline.append({
                        "word": token,
                        "start": w_start,
                        "end": w_end,
                        "index": i
                    })
            return timeline

    # Fallback to pure whisper words if no reference text
    out_timeline = []
    for i, item in enumerate(whisper_words):
        out_timeline.append({
            "word": item["word"],
            "start": item["start"],
            "end": item["end"],
            "index": i
        })
    return out_timeline


def save_timeline(timeline: List[Dict[str, Any]], filepath: str):
    """Saves word timeline to JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(timeline, f, ensure_ascii=False, indent=2)
