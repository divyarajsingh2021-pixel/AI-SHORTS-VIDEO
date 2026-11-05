"""
Micro-Shot Planning Engine.
Splits the word timeline into micro-shots of 5 to 9 words (~2-3 seconds each).
Ensures 1 visual idea per shot, concrete physical visual prompt, keywords,
camera motion, and exact key_word synchronization anchor.
Supports Ollama (qwen2.5:1.5b) with fast rule-based fallback and pydantic validation.
"""

from typing import List, Dict, Any, Optional
import json
import urllib.request
import re
from pydantic import BaseModel, Field

class MicroShot(BaseModel):
    shot_id: int
    narration_text: str
    start_word_index: int
    end_word_index: int
    start_time: float
    end_time: float
    visual_prompt: str
    negative_prompt: str = "text, watermark, blurry, low quality, distorted, extra limbs, abstract shapes"
    keywords: List[str] = Field(default_factory=list)
    key_word: str
    camera_motion: str = "zoom_in"  # zoom_in, zoom_out, pan_right, pan_left
    transition: str = "crossfade"


STYLE_BIBLE = {
    "cinematic": "cinematic hyper-realistic photography, dramatic volumetric golden hour lighting, 8k resolution, photorealistic, 9:16 vertical framing",
    "anime": "vibrant anime cinematic style, Makoto Shinkai aesthetic, detailed background, dynamic lighting, 9:16 vertical framing",
    "cyberpunk": "futuristic cyberpunk city, neon glowing lights, misty night atmosphere, sharp reflections, 9:16 vertical framing",
    "historical": "ancient epic historical setting, rich textured stone architecture, atmospheric dust particles, warm mystical lighting, 9:16 vertical framing",
    "dark_documentary": "moody investigative documentary style, high contrast shadows, film grain, muted palette, 9:16 vertical framing"
}


# Mapping of concrete concepts for translation/conversion from Hindi or abstract terms
CONCEPT_DICTIONARY = {
    "जगन्नाथ": "grand ancient Jagannath Temple in Puri, towering stone temple spire, sacred atmosphere",
    "पुरी": "Puri coastal ancient city with sacred temple architecture",
    "मंदिर": "majestic ancient Indian temple with carved stone pillars and sanctum",
    "ध्वज": "sacred red silk triangular flag fluttering on top of temple spire against turbulent ocean wind",
    "हवा": "intense ocean winds blowing across coastal sky",
    "परछाई": "bright midday sun casting direct overhead illumination on stone pavement, zero shadow",
    "गुंबद": "colossal ancient temple stone dome with ornate carvings against pure sky",
    "पक्षी": "clear mystical sky above temple summit with flying birds only far on the perimeter",
    "विमान": "high altitude pure blue sky with no airplanes visible above temple sanctum",
    "सिंहद्वार": "imposing stone lion gate entrance of temple with guardian statues",
    "समुद्र": "roaring ocean waves crashing on nearby beach coastline",
    "महाप्रसाद": "sacred traditional Indian feast, steaming clay pots",
    "बर्तन": "seven rustic ancient earthenware clay pots stacked vertically over firewood flame, steam rising from top pot",
    "चमत्कार": "awe-inspiring divine temple miracle, mystical golden aura",
    "विज्ञान": "ancient stone mystery defying modern scientific understanding",
    "शिखर": "towering summit spire of ancient temple reaching into clouds",
    "कदम": "stepping across ancient carved stone threshold into temple hall",
    "आवाज": "peaceful silent temple sanctum contrasting with roaring sea outside",
    "fire": "crackling golden wood fire heating traditional cooking pots",
    "space": "deep cosmic space with glowing nebula and distant stars",
    "earth": "planet Earth glowing against the black void of space",
    "growth": "a small green plant sprouting through cracked dry soil, macro lens focus"
}


def _extract_concrete_keywords(text: str) -> List[str]:
    """Finds nouns and concrete visual anchors from text."""
    words = re.findall(r'[\w]+', text)
    matched = []
    for w in words:
        w_lower = w.lower()
        for k in CONCEPT_DICTIONARY:
            if k in w_lower or w_lower in k:
                if k not in matched:
                    matched.append(k)
    if not matched:
        # Take first 3 nouns/significant words
        matched = [w for w in words if len(w) > 3][:3]
    return matched[:4]


def _build_rule_based_shot(
    shot_id: int,
    words_slice: List[Dict[str, Any]],
    art_style: str = "cinematic"
) -> MicroShot:
    """Fast deterministic generator for micro-shot when LLM is slow or offline."""
    narration = " ".join(w["word"] for w in words_slice)
    start_time = words_slice[0]["start"]
    end_time = words_slice[-1]["end"]
    start_idx = words_slice[0]["index"]
    end_idx = words_slice[-1]["index"]
    
    keywords = _extract_concrete_keywords(narration)
    key_word = keywords[0] if keywords else (words_slice[len(words_slice)//2]["word"])
    
    # Generate concrete visual prompt
    visual_ideas = []
    for kw in keywords:
        if kw in CONCEPT_DICTIONARY:
            visual_ideas.append(CONCEPT_DICTIONARY[kw])
            
    if visual_ideas:
        base_visual = ", ".join(visual_ideas[:2])
    else:
        base_visual = f"Cinematic detailed visual depicting {narration}"
        
    style_suffix = STYLE_BIBLE.get(art_style, STYLE_BIBLE["cinematic"])
    final_prompt = f"{base_visual}, {style_suffix}"
    
    # Camera motion alternates to maintain fast TikTok/Shorts pacing
    motions = ["zoom_in", "zoom_out", "pan_right", "zoom_in"]
    motion = motions[shot_id % len(motions)]
    
    return MicroShot(
        shot_id=shot_id,
        narration_text=narration,
        start_word_index=start_idx,
        end_word_index=end_idx,
        start_time=start_time,
        end_time=end_time,
        visual_prompt=final_prompt,
        keywords=keywords,
        key_word=key_word,
        camera_motion=motion,
        transition="crossfade"
    )


def plan_micro_shots(
    timeline: List[Dict[str, Any]],
    art_style: str = "cinematic",
    min_words: int = 5,
    max_words: int = 9,
    ollama_url: str = "http://127.0.0.1:11434",
    ollama_model: str = "qwen2.5:1.5b",
    try_ollama: bool = False,
    min_shot_duration: float = 2.5,
    max_shot_duration: float = 3.5,
) -> List[MicroShot]:
    """
    Groups words from timeline into 5-9 word shots.
    Ensures a minimum number of shots based on audio length.
    Falls back to a deterministic splitter if needed.
    """
    if not timeline:
        return []

    # 1. Chunk words into slices of target word count (5-8 words per shot)
    shots: List[MicroShot] = []
    current_chunk = []

    for word_info in timeline:
        current_chunk.append(word_info)
        # End chunk if reached target size or sentence boundary
        is_punct = word_info["word"].endswith(('.', '!', '?', '।', '|', ':'))
        if len(current_chunk) >= max_words or (len(current_chunk) >= min_words and is_punct):
            shots.append(_build_rule_based_shot(len(shots), current_chunk, art_style))
            current_chunk = []

    if current_chunk:
        if shots and len(current_chunk) < min_words:
            # Merge with last shot if too short
            last = shots[-1]
            last_words = timeline[last.start_word_index : current_chunk[-1]["index"] + 1]
            shots[-1] = _build_rule_based_shot(last.shot_id, last_words, art_style)
        else:
            shots.append(_build_rule_based_shot(len(shots), current_chunk, art_style))

    # Ensure no shot exceeds 3.5s without visual cut; split if needed
    normalized_shots: List[MicroShot] = []
    for s in shots:
        dur = s.end_time - s.start_time
        if dur > max_shot_duration and (s.end_word_index - s.start_word_index) >= 8:
            # Split in half
            mid_idx = (s.start_word_index + s.end_word_index) // 2
            slice1 = timeline[s.start_word_index : mid_idx + 1]
            slice2 = timeline[mid_idx + 1 : s.end_word_index + 1]
            if slice1 and slice2:
                normalized_shots.append(_build_rule_based_shot(len(normalized_shots), slice1, art_style))
                normalized_shots.append(_build_rule_based_shot(len(normalized_shots), slice2, art_style))
                continue
        normalized_shots.append(s)

    # Re-index shot IDs sequentially
    for i, s in enumerate(normalized_shots):
        s.shot_id = i

    # ---------- Minimum shot validation & deterministic fallback ----------
    # Compute audio duration from the last word timestamp
    audio_duration = timeline[-1]["end"] if timeline else 0.0
    min_shots_needed = int((audio_duration // max_shot_duration) + 1)
    if len(normalized_shots) < min_shots_needed:
        # Deterministic fallback: split raw narration by punctuation and then into 6‑9 word chunks
        raw_text = " ".join(w["word"] for w in timeline)
        words = raw_text.split()
        fallback_chunks: List[List[Dict[str, Any]]] = []
        idx = 0
        while idx < len(words):
            chunk_len = min(max_words, max(min_words, len(words) - idx))
            chunk_words = words[idx: idx + chunk_len]
            # Build slice dicts mimicking original timeline (approx timestamps)
            slice_info = []
            start_time = timeline[idx]["start"] if idx < len(timeline) else 0.0
            for offset, w in enumerate(chunk_words):
                slice_info.append({
                    "word": w,
                    "start": start_time + offset * 0.3,
                    "end": start_time + (offset + 1) * 0.3,
                    "index": idx + offset,
                })
            fallback_chunks.append(slice_info)
            idx += chunk_len
        # Build shots from fallback chunks
        fallback_shots: List[MicroShot] = []
        for chunk in fallback_chunks:
            fallback_shots.append(_build_rule_based_shot(len(fallback_shots), chunk, art_style))
        normalized_shots = fallback_shots
        # Re‑index again
        for i, s in enumerate(normalized_shots):
            s.shot_id = i

    return normalized_shots
    """
    Groups words from timeline into 5-9 word shots.
    Each shot represents exactly one visual beat.
    """
    if not timeline:
        return []
        
    # 1. Chunk words into slices of target word count (5-8 words per shot)
    shots: List[MicroShot] = []
    current_chunk = []
    
    for word_info in timeline:
        current_chunk.append(word_info)
        # End chunk if reached target size or sentence boundary
        is_punct = word_info["word"].endswith(('.', '!', '?', '।', '|', ':'))
        if len(current_chunk) >= max_words or (len(current_chunk) >= min_words and is_punct):
            shots.append(_build_rule_based_shot(len(shots), current_chunk, art_style))
            current_chunk = []
            
    if current_chunk:
        if shots and len(current_chunk) < min_words:
            # Merge with last shot if too short
            last = shots[-1]
            last_words = timeline[last.start_word_index : current_chunk[-1]["index"] + 1]
            shots[-1] = _build_rule_based_shot(last.shot_id, last_words, art_style)
        else:
            shots.append(_build_rule_based_shot(len(shots), current_chunk, art_style))

    # Ensure no shot exceeds 3.5s without visual cut; split if needed
    normalized_shots: List[MicroShot] = []
    for s in shots:
        dur = s.end_time - s.start_time
        if dur > 4.2 and (s.end_word_index - s.start_word_index) >= 8:
            # Split in half
            mid_idx = (s.start_word_index + s.end_word_index) // 2
            slice1 = timeline[s.start_word_index : mid_idx + 1]
            slice2 = timeline[mid_idx + 1 : s.end_word_index + 1]
            if slice1 and slice2:
                normalized_shots.append(_build_rule_based_shot(len(normalized_shots), slice1, art_style))
                normalized_shots.append(_build_rule_based_shot(len(normalized_shots), slice2, art_style))
                continue
        normalized_shots.append(s)

    # Re-index shot IDs sequentially
    for i, s in enumerate(normalized_shots):
        s.shot_id = i

    return normalized_shots
