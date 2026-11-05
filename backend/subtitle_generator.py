import re
from pathlib import Path
from typing import List, Dict, Any
from config import SUBTITLE_STYLES, VIDEO_WIDTH, VIDEO_HEIGHT

def format_ass_time(seconds: float) -> str:
    """Formats seconds into ASS timestamp format: H:MM:SS.cc"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis >= 100:
        centis = 99
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"

class SubtitleGenerator:
    """Generates viral, animated, word-level highlighted ASS subtitle files."""

    @staticmethod
    def create_ass_subtitles_from_timeline(
        timeline: List[Dict[str, Any]],
        output_ass_path: Path,
        style_key: str = "hormozi",
        words_per_group: int = 3
    ) -> Path:
        """
        Creates an Advanced SubStation Alpha (.ass) subtitle file using timeline.json
        word timestamps for 1:1 master clock synchronization.
        """
        output_ass_path = Path(output_ass_path)
        output_ass_path.parent.mkdir(parents=True, exist_ok=True)

        style = SUBTITLE_STYLES.get(style_key, SUBTITLE_STYLES["hormozi"])

        # Check if text contains Devanagari (Hindi)
        has_devanagari = any(bool(re.search(r'[\u0900-\u097F]', w.get("word", ""))) for w in timeline)
        font_name = "Nirmala UI" if has_devanagari else style['font']

        # ASS Header
        header = f"""[Script Info]
Title: 1:1 Synchronized AI Shorts Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: {VIDEO_WIDTH}
PlayResY: {VIDEO_HEIGHT}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{style['fontsize']},{style['primary_color']},{style['highlight_color']},{style['outline_color']},{style['outline_color']},-1,0,0,0,100,100,2,0,1,{style['outline']},{style['shadow']},{style['alignment']},60,60,{style['margin_v']},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events = []

        if not timeline:
            return output_ass_path

        # Group words into chunks of 2-4 words for fast Shorts readability
        groups = []
        for i in range(0, len(timeline), words_per_group):
            group = timeline[i:i + words_per_group]
            if group:
                groups.append(group)

        for group in groups:
            group_start = group[0]["start"]
            group_end = group[-1]["end"] + 0.15

            # Word-level karaoke pop
            for idx, active_word in enumerate(group):
                w_start = format_ass_time(active_word["start"])
                if idx + 1 < len(group):
                    w_end = format_ass_time(group[idx + 1]["start"])
                else:
                    w_end = format_ass_time(group_end)

                formatted_tokens = []
                for w_idx, w in enumerate(group):
                    word_str = w["word"].upper()
                    word_str = re.sub(r'[{}\\]', '', word_str)

                    if w_idx == idx:
                        # Highlight active word + slight zoom punch
                        formatted_tokens.append(
                            f"{{\\c{style['highlight_color']}\\fscx115\\fscy115}}{word_str}{{\\r}}"
                        )
                    else:
                        formatted_tokens.append(
                            f"{{\\c{style['primary_color']}}}{word_str}{{\\r}}"
                        )

                line_text = " ".join(formatted_tokens)
                events.append(f"Dialogue: 0,{w_start},{w_end},Default,,0,0,0,,{line_text}")

        full_ass_content = header + "\n".join(events) + "\n"
        with open(output_ass_path, "w", encoding="utf-8") as f:
            f.write(full_ass_content)

        return output_ass_path

    @classmethod
    def create_ass_subtitles(
        cls,
        scenes: List[Dict[str, Any]],
        output_ass_path: Path,
        style_key: str = "hormozi",
        words_per_group: int = 3
    ) -> Path:
        """Legacy compatibility wrapper for scene-based data."""
        all_words = []
        for s in scenes:
            all_words.extend(s.get("words", []))
        return cls.create_ass_subtitles_from_timeline(all_words, output_ass_path, style_key, words_per_group)
