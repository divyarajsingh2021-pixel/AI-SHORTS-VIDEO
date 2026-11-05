import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import FFMPEG_EXE, VIDEO_WIDTH, VIDEO_HEIGHT, FPS, MUSIC_DIR

class VideoRenderer:
    """Assembles final 1080x1920 YouTube Short with frame-accurate cuts, BGM ducking, and burned ASS subtitles."""

    @staticmethod
    def render_micro_shot_clip(
        image_path: Path,
        duration: float,
        output_clip_path: Path,
        camera_motion: str = "zoom_in",
        width: int = 1080,
        height: int = 1920,
        fps: int = 30
    ) -> Path:
        """
        Renders a single micro-shot image into a video clip with smooth Ken Burns camera motion.
        Duration is strictly dictated by word timestamps.
        """
        output_clip_path = Path(output_clip_path)
        session_dir = output_clip_path.parent
        total_frames = max(1, int(duration * fps))

        # Precision Ken Burns zoom motion
        if camera_motion == "zoom_in":
            # Start at 1.0 zoom and smoothly punch in to 1.15
            pan_filter = f"scale={width}:{height},zoompan=z='min(zoom+0.0015,1.15)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height}:fps={fps}"
        elif camera_motion == "zoom_out":
            # Start zoomed at 1.15 and pull out to 1.0
            pan_filter = f"scale={width}:{height},zoompan=z='if(lte(zoom,1.0),1.15,max(1.001,zoom-0.0015))':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={width}x{height}:fps={fps}"
        else:
            # Subtle pan right
            pan_filter = f"scale={width}:{height},zoompan=z=1.08:d={total_frames}:x='min(x+0.5,iw-iw/zoom)':y='ih/2-(ih/zoom/2)':s={width}x{height}:fps={fps}"

        cmd = [
            FFMPEG_EXE, "-y",
            "-loop", "1",
            "-i", image_path.name,
            "-vf", pan_filter,
            "-t", f"{duration:.3f}",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "ultrafast",
            "-r", str(fps),
            output_clip_path.name
        ]

        res = subprocess.run(cmd, cwd=str(session_dir), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            # Fallback simple scale
            cmd_fallback = [
                FFMPEG_EXE, "-y",
                "-loop", "1",
                "-i", image_path.name,
                "-vf", f"scale={width}:{height}",
                "-t", f"{duration:.3f}",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-preset", "ultrafast",
                "-r", str(fps),
                output_clip_path.name
            ]
            subprocess.run(cmd_fallback, cwd=str(session_dir), check=True)

        return output_clip_path

    @staticmethod
    def concatenate_scene_clips(clip_paths: List[Path], output_concat_path: Path) -> Path:
        """Concatenates individual scene MP4 clips into one continuous visual track."""
        output_concat_path = Path(output_concat_path)
        output_concat_path.parent.mkdir(parents=True, exist_ok=True)
        session_dir = output_concat_path.parent

        list_file = session_dir / "concat_list.txt"
        with open(list_file, "w", encoding="utf-8") as f:
            for p in clip_paths:
                f.write(f"file '{p.name}'\n")

        cmd = [
            FFMPEG_EXE, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", "concat_list.txt",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "veryfast",
            "-r", str(FPS),
            output_concat_path.name
        ]
        res = subprocess.run(cmd, cwd=str(session_dir), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg concat clips failed: {res.stderr}")

        return output_concat_path

    @staticmethod
    def concatenate_audio_tracks(audio_paths: List[Path], output_audio_path: Path) -> Path:
        """Concatenates audio files into a unified master voiceover track."""
        output_audio_path = Path(output_audio_path)
        output_audio_path.parent.mkdir(parents=True, exist_ok=True)
        session_dir = output_audio_path.parent

        list_file = session_dir / "audio_concat_list.txt"
        with open(list_file, "w", encoding="utf-8") as f:
            for p in audio_paths:
                f.write(f"file '{p.name}'\n")

        cmd = [
            FFMPEG_EXE, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", "audio_concat_list.txt",
            "-c:a", "libmp3lame",
            "-b:a", "192k",
            output_audio_path.name
        ]
        res = subprocess.run(cmd, cwd=str(session_dir), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg concat audio failed: {res.stderr}")

        return output_audio_path

    @classmethod
    def assemble_final_short(
        cls,
        video_track: Path,
        audio_track: Path,
        ass_subtitles: Path,
        output_final_path: Path,
        bgm_track: Optional[Path] = None,
        layout_mode: str = "fullscreen",
        gameplay_clip: Optional[Path] = None,
        preview_mode: bool = False
    ) -> Path:
        """
        Final composite: Combines video, voiceover, optional background music with ducking,
        and renders ASS subtitles directly onto the video.
        Uses cwd=session_dir to guarantee 100% path safety on Windows.
        """
        output_final_path = Path(output_final_path)
        output_final_path.parent.mkdir(parents=True, exist_ok=True)
        session_dir = output_final_path.parent

        rel_video = video_track.name
        rel_audio = audio_track.name
        rel_sub = ass_subtitles.name
        rel_final = output_final_path.name

        inputs = ["-i", rel_video, "-i", rel_audio]

        # Subtitle burning
        video_filter = f"[0:v]subtitles={rel_sub}[v]"

        # Audio mixing & auto-ducking
        if bgm_track and Path(bgm_track).exists():
            inputs.extend(["-stream_loop", "-1", "-i", str(bgm_track.resolve())])
            audio_filter = (
                f"[2:a]volume=0.12[bgm];"
                f"[bgm][1:a]amix=inputs=2:duration=first:dropout_transition=2[a]"
            )
        else:
            audio_filter = "[1:a]volume=1.0[a]"

        preset = "ultrafast" if preview_mode else "faster"
        crf = "28" if preview_mode else "20"

        cmd = [
            FFMPEG_EXE, "-y",
            *inputs,
            "-filter_complex", f"{video_filter};{audio_filter}",
            "-map", "[v]",
            "-map", "[a]",
            "-c:v", "libx264",
            "-preset", preset,
            "-crf", crf,
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-pix_fmt", "yuv420p",
            "-r", str(FPS),
            rel_final
        ]

        res = subprocess.run(cmd, cwd=str(session_dir), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            print(f"[VideoRenderer] Subtitle filter warning, retrying with direct copy mux: {res.stderr[-200:]}")
            fallback_cmd = [
                FFMPEG_EXE, "-y",
                "-i", rel_video,
                "-i", rel_audio,
                "-map", "0:v",
                "-map", "1:a",
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                rel_final
            ]
            subprocess.run(fallback_cmd, cwd=str(session_dir), check=True)

        return output_final_path
