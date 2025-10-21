"""
Pydantic models for subtitle generation MVP
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class SilenceSegment(BaseModel):
    """無音区間を表すモデル"""
    start: float = Field(..., description="無音開始時刻（秒）")
    end: float = Field(..., description="無音終了時刻（秒）")


class ProcessResponse(BaseModel):
    """API レスポンスモデル"""
    srt_text: str = Field(..., description="生成されたSRT字幕テキスト")
    silence_segments: List[SilenceSegment] = Field(..., description="検出された無音区間リスト")
    removed_fillers: Optional[List[str]] = Field(default=None, description="削除されたフィラーワードリスト")


class ProcessRequest(BaseModel):
    """処理リクエストのパラメータ"""
    silence_threshold_db: float = Field(default=-35.0, description="無音判定の閾値（dB）")
    min_silence_sec: float = Field(default=0.35, description="無音と判定する最小秒数")
    profile: Optional[str] = Field(default="talk_default", description="使用するプロファイル名")

