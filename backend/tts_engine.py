import os
import re
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Tuple
import edge_tts
from faster_whisper import WhisperModel

# Lazy load whisper model to optimize startup time
_whisper_model = None

# Known local cache paths for instant offline loading without network hangs
LOCAL_WHISPER_PATH = Path(r"C:\Users\hp\.cache\huggingface\hub\models--Systran--faster-whisper-tiny\snapshots\d90ca5fe260221311c53c58e660288d3deb8d356")

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        try:
            if LOCAL_WHISPER_PATH.exists():
                _whisper_model = WhisperModel(str(LOCAL_WHISPER_PATH), device="cpu", compute_type="int8", cpu_threads=4)
            else:
                _whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8", cpu_threads=4, local_files_only=False)
        except Exception as e:
            print(f"[TTSEngine] Error initializing faster-whisper: {e}")
            _whisper_model = None
    return _whisper_model

class TTSEngine:
    """Free Edge-TTS generator + Faster-Whisper millisecond word alignment engine."""

    @staticmethod
    async def generate_speech_file(text: str, voice: str, output_path: Path, rate: str = "+0%", pitch: str = "+0Hz"):
        """Generates an MP3 file using Microsoft Edge Neural TTS."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            pitch=pitch
        )
        await communicate.save(str(output_path))
        return output_path

    @staticmethod
    def align_words_with_whisper(audio_path: Path, fallback_text: str = "") -> Tuple[float, List[Dict[str, Any]]]:
        """
        Transcribes audio with faster-whisper and extracts word-level start/end timestamps.
        If fallback_text contains non-Latin scripts (e.g. Hindi Devanagari), maps the
        authentic native words to the audio timestamps for accurate on-screen display.
        """
        model = get_whisper_model()
        all_words = []
        duration = 3.0

        # Check if text is Hindi / Devanagari
        is_hindi = bool(re.search(r'[\u0900-\u097F]', fallback_text))
        lang = "hi" if is_hindi else "en"

        if model is not None:
            try:
                segments, info = model.transcribe(
                    str(audio_path),
                    word_timestamps=True,
                    language=lang
                )
                duration = info.duration
                for segment in segments:
                    if segment.words:
                        for w in segment.words:
                            clean_word = w.word.strip()
                            if clean_word:
                                all_words.append({
                                    "word": clean_word,
                                    "start": round(w.start, 2),
                                    "end": round(w.end, 2)
                                })
            except Exception as e:
                print(f"[TTSEngine] Whisper transcription exception: {e}")

        # If text is Hindi or whisper returned transliteration/empty, ensure authentic original words
        if fallback_text and (is_hindi or not all_words):
            raw_words = [w.strip() for w in re.split(r'\s+', fallback_text) if w.strip()]
            num_words = len(raw_words)
            if num_words > 0:
                step = duration / num_words
                devanagari_words = []
                for idx, rw in enumerate(raw_words):
                    devanagari_words.append({
                        "word": rw,
                        "start": round(idx * step, 2),
                        "end": round((idx + 1) * step, 2)
                    })
                all_words = devanagari_words

        return duration, all_words

    @classmethod
    async def process_scenes(
        cls,
        scenes: List[Dict[str, Any]],
        voice: str,
        session_dir: Path,
        voice_speed: str = "+0%"
    ) -> Dict[str, Any]:
        """
        Generates speech for each scene individually to ensure 100% 1:1 sync,
        and also generates individual scene audio files + full concatenated metadata.
        Supports custom voice playback rate (e.g. +15% for viral shorts).
        """
        session_dir = Path(session_dir)
        session_dir.mkdir(parents=True, exist_ok=True)

        processed_scenes = []
        cumulative_time = 0.0

        for i, scene in enumerate(scenes):
            scene_text = scene["text"]
            audio_filename = f"scene_{i+1:02d}.mp3"
            scene_audio_path = session_dir / audio_filename

            # 1. Synthesize audio for this scene with voice speed
            await cls.generate_speech_file(scene_text, voice, scene_audio_path, rate=voice_speed)

            # 2. Extract word-level timestamps using Whisper
            duration, words = cls.align_words_with_whisper(scene_audio_path, fallback_text=scene_text)

            # Add a slight padding (0.2s) at end of scene for natural breathing room
            scene_duration = max(round(duration + 0.2, 2), 1.5)

            # Map word timestamps to absolute timeline offsets
            absolute_words = []
            for w in words:
                absolute_words.append({
                    "word": w["word"],
                    "start": round(cumulative_time + w["start"], 2),
                    "end": round(cumulative_time + w["end"], 2),
                    "relative_start": w["start"],
                    "relative_end": w["end"]
                })

            scene_copy = dict(scene)
            scene_copy["audio_file"] = str(scene_audio_path)
            scene_copy["audio_filename"] = audio_filename
            scene_copy["start_time"] = round(cumulative_time, 2)
            scene_copy["duration"] = scene_duration
            scene_copy["end_time"] = round(cumulative_time + scene_duration, 2)
            scene_copy["words"] = absolute_words
            scene_copy["local_words"] = words

            processed_scenes.append(scene_copy)
            cumulative_time += scene_duration

        return {
            "total_duration": round(cumulative_time, 2),
            "scenes": processed_scenes
        }
