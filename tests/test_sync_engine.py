import pytest
import os
import json
from pathlib import Path
from backend.timeline_engine import build_audio_timeline
from backend.shot_planner import plan_micro_shots, _extract_concrete_keywords, _build_rule_based_shot

def test_extract_concrete_keywords():
    text = "ओडिशा के जगन्नाथ पुरी मंदिर के शिखर पर लगा ध्वज हवा की उल्टी दिशा में लहराता है"
    kws = _extract_concrete_keywords(text)
    assert len(kws) > 0
    assert any(k in ["जगन्नाथ", "मंदिर", "ध्वज", "हवा", "शिखर"] for k in kws)

def test_plan_micro_shots_chunking():
    # Mock a 20-word timeline
    mock_timeline = [
        {"word": f"word_{i}", "start": round(i * 0.4, 2), "end": round((i + 1) * 0.4, 2), "index": i}
        for i in range(25)
    ]
    shots = plan_micro_shots(mock_timeline, art_style="cinematic", min_words=5, max_words=8)
    
    # 25 words split into 5-8 words chunks should give 3 to 5 micro-shots
    assert len(shots) >= 3
    assert len(shots) <= 6
    
    # Verify continuity
    for i in range(len(shots) - 1):
        assert shots[i].end_time <= shots[i+1].start_time + 0.1
        assert shots[i].end_word_index + 1 == shots[i+1].start_word_index

def test_rule_based_shot_visual_prompt():
    slice_words = [
        {"word": "मंदिर", "start": 0.0, "end": 0.5, "index": 0},
        {"word": "का", "start": 0.5, "end": 0.8, "index": 1},
        {"word": "ध्वज", "start": 0.8, "end": 1.2, "index": 2},
        {"word": "हवा", "start": 1.2, "end": 1.6, "index": 3},
        {"word": "में", "start": 1.6, "end": 2.0, "index": 4},
    ]
    shot = _build_rule_based_shot(0, slice_words, "cinematic")
    assert "temple" in shot.visual_prompt.lower() or "flag" in shot.visual_prompt.lower()
    assert shot.camera_motion in ["zoom_in", "zoom_out", "pan_right"]
