"""
Core processing module for subtitle generation MVP
- Whisper API for speech-to-text
- Filler word removal
- Silence detection using FFmpeg
"""
import os
import re
import json
import subprocess
from typing import List, Dict, Tuple
from openai import OpenAI


# 日本語フィラーワード辞書
FILLER_WORDS = [
    "えー", "あのー", "えっと", "そのー", "まー", "えぇと",
    "あー", "うー", "んー", "ええ", "あの", "その", "まあ"
]


def transcribe_audio_with_whisper(audio_path: str) -> List[Dict]:
    """
    Whisper APIを使用して音声を文字起こし
    
    Args:
        audio_path: 音声ファイルのパス
        
    Returns:
        タイムスタンプ付きのトランスクリプトセグメントリスト
    """
    client = OpenAI()  # 環境変数 OPENAI_API_KEY を使用
    
    with open(audio_path, "rb") as audio_file:
        # Whisper APIでタイムスタンプ付き文字起こし
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
            timestamp_granularities=["segment"]
        )
    
    # セグメント情報を抽出
    segments = []
    if hasattr(transcript, 'segments') and transcript.segments:
        for seg in transcript.segments:
            segments.append({
                "start": seg.get("start", 0.0),
                "end": seg.get("end", 0.0),
                "text": seg.get("text", "").strip()
            })
    else:
        # セグメント情報がない場合は全体テキストを1つのセグメントとして扱う
        segments.append({
            "start": 0.0,
            "end": 0.0,
            "text": transcript.text.strip()
        })
    
    return segments


def remove_filler_words(text: str, filler_words: List[str] = None) -> str:
    """
    テキストからフィラーワードを削除
    
    Args:
        text: 元のテキスト
        filler_words: 削除するフィラーワードのリスト
        
    Returns:
        フィラーワードを削除したテキスト
    """
    if filler_words is None:
        filler_words = FILLER_WORDS
    
    cleaned_text = text
    
    # 各フィラーワードを削除（大文字小文字を区別しない）
    for filler in filler_words:
        # 単語境界を考慮したパターン
        pattern = re.compile(re.escape(filler), re.IGNORECASE)
        cleaned_text = pattern.sub("", cleaned_text)
    
    # 連続する空白を1つにまとめる
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    
    # 前後の空白を削除
    cleaned_text = cleaned_text.strip()
    
    return cleaned_text


def detect_silence(
    video_path: str,
    noise_threshold_db: float = -35.0,
    min_silence_duration: float = 0.35
) -> List[Dict[str, float]]:
    """
    FFmpegのsilencedetectフィルタを使用して無音区間を検出
    
    Args:
        video_path: 動画ファイルのパス
        noise_threshold_db: 無音判定の閾値（dB）
        min_silence_duration: 無音と判定する最小秒数
        
    Returns:
        無音区間のリスト [{"start": 1.23, "end": 2.56}, ...]
    """
    # FFmpegコマンドを構築
    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-af", f"silencedetect=noise={noise_threshold_db}dB:d={min_silence_duration}",
        "-f", "null",
        "-"
    ]
    
    # FFmpegを実行（stderrに結果が出力される）
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )
    
    # stderrから無音区間を抽出
    silence_segments = []
    silence_start = None
    
    for line in result.stderr.split('\n'):
        # silence_start を検出
        if 'silence_start:' in line:
            match = re.search(r'silence_start:\s*([\d.]+)', line)
            if match:
                silence_start = float(match.group(1))
        
        # silence_end を検出
        if 'silence_end:' in line and silence_start is not None:
            match = re.search(r'silence_end:\s*([\d.]+)', line)
            if match:
                silence_end = float(match.group(1))
                silence_segments.append({
                    "start": silence_start,
                    "end": silence_end
                })
                silence_start = None
    
    return silence_segments


def generate_srt(segments: List[Dict], filler_words: List[str] = None) -> str:
    """
    セグメントリストからSRT形式の字幕テキストを生成
    
    Args:
        segments: タイムスタンプとテキストを含むセグメントリスト
        filler_words: 削除するフィラーワードのリスト
        
    Returns:
        SRT形式の字幕テキスト
    """
    srt_lines = []
    
    for idx, seg in enumerate(segments, start=1):
        # フィラーワードを削除
        cleaned_text = remove_filler_words(seg["text"], filler_words)
        
        # 空のテキストはスキップ
        if not cleaned_text:
            continue
        
        # タイムスタンプをSRT形式に変換
        start_time = format_srt_timestamp(seg["start"])
        end_time = format_srt_timestamp(seg["end"])
        
        # SRTエントリを追加
        srt_lines.append(f"{idx}")
        srt_lines.append(f"{start_time} --> {end_time}")
        srt_lines.append(cleaned_text)
        srt_lines.append("")  # 空行
    
    return "\n".join(srt_lines)


def format_srt_timestamp(seconds: float) -> str:
    """
    秒数をSRT形式のタイムスタンプに変換
    
    Args:
        seconds: 秒数
        
    Returns:
        SRT形式のタイムスタンプ（例: 00:00:01,500）
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def transcribe_to_srt(video_path: str, filler_words: List[str] = None) -> Tuple[str, List[Dict]]:
    """
    動画ファイルを文字起こししてSRT字幕を生成
    
    Args:
        video_path: 動画ファイルのパス
        filler_words: 削除するフィラーワードのリスト
        
    Returns:
        (SRT字幕テキスト, セグメントリスト)
    """
    # Whisper APIで文字起こし
    segments = transcribe_audio_with_whisper(video_path)
    
    # SRT字幕を生成（フィラーワード削除を含む）
    srt_text = generate_srt(segments, filler_words)
    
    return srt_text, segments


def process_video(
    video_path: str,
    silence_threshold_db: float = -35.0,
    min_silence_sec: float = 0.35,
    filler_words: List[str] = None
) -> Tuple[str, List[Dict[str, float]]]:
    """
    動画ファイルを処理して字幕と無音区間を生成
    
    Args:
        video_path: 動画ファイルのパス
        silence_threshold_db: 無音判定の閾値（dB）
        min_silence_sec: 無音と判定する最小秒数
        filler_words: 削除するフィラーワードのリスト
        
    Returns:
        (SRT字幕テキスト, 無音区間リスト)
    """
    # 1. Whisper APIで文字起こし＋SRT生成
    srt_text, segments = transcribe_to_srt(video_path, filler_words)
    
    # 2. 無音区間を検出
    silence_segments = detect_silence(
        video_path,
        silence_threshold_db,
        min_silence_sec
    )
    
    return srt_text, silence_segments

