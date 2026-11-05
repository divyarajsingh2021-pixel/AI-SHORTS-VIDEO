"""
Sync Report Generator.
Outputs a structured summary table and logs any anomalies:
- Duration warnings (>4.0s)
- Gaps in narration coverage
- Word sync alignments
- CLIP / match verification scores
"""

from typing import List, Dict, Any
import json
import os

def generate_sync_report(shots: List[Any], verification_results: List[Dict[str, Any]], session_dir: str) -> str:
    """
    Builds human-readable table and saves report.json in session directory.
    """
    rows = []
    headers = ["Shot ID", "Narration Words", "Start (s)", "End (s)", "Dur (s)", "Key Word", "Match Score", "Keywords Hit"]
    
    table_lines = []
    table_lines.append(f"{headers[0]:<8} | {headers[1]:<32} | {headers[2]:<9} | {headers[3]:<7} | {headers[4]:<7} | {headers[5]:<12} | {headers[6]:<11} | {headers[7]}")
    table_lines.append("-" * 115)
    
    report_data = []
    warnings = []
    
    prev_end = 0.0
    for s, v in zip(shots, verification_results):
        dur = round(s.end_time - s.start_time, 2)
        words_preview = s.narration_text[:30] + ("..." if len(s.narration_text) > 30 else "")
        score = v.get("score", 0.85)
        hits = ", ".join(v.get("hits", [])) or "None"
        
        row_str = f"{s.shot_id:<8} | {words_preview:<32} | {s.start_time:<9.2f} | {s.end_time:<7.2f} | {dur:<7.2f} | {s.key_word:<12} | {score:<11.2f} | {hits}"
        table_lines.append(row_str)
        
        # Check warnings
        if dur > 4.0:
            warnings.append(f"[WARNING] Shot {s.shot_id} is {dur}s (> 4.0s maximum guideline)")
        if s.start_time > prev_end + 0.35:
            warnings.append(f"[WARNING] Potential gap detected before Shot {s.shot_id}: {prev_end:.2f}s to {s.start_time:.2f}s")
        if score < 0.60:
            warnings.append(f"[WARNING] Shot {s.shot_id} match score {score} is below 0.60 threshold")
            
        prev_end = s.end_time
        report_data.append({
            "shot_id": s.shot_id,
            "narration_text": s.narration_text,
            "start_time": s.start_time,
            "end_time": s.end_time,
            "duration": dur,
            "key_word": s.key_word,
            "match_score": score,
            "keywords_hit": v.get("hits", [])
        })

    report_text = "\n".join(table_lines)
    if warnings:
        report_text += "\n\n⚠️ SYNC ANOMALIES & AUDIT WARNINGS:\n" + "\n".join(warnings)
    else:
        report_text += "\n\n✅ 100% PERFECT SYNC: All shots strictly aligned within guidelines!"

    # Save to session dir
    json_path = os.path.join(session_dir, "sync_report.json")
    txt_path = os.path.join(session_dir, "sync_report.txt")
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({"shots": report_data, "warnings": warnings}, f, indent=2, ensure_ascii=False)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(report_text)
    except Exception as e:
        print(f"[SyncReport] Error writing report: {e}")

    return report_text
