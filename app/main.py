"""
FastAPI application for subtitle generation MVP (おまかせ版 v7)
"""
import os
import tempfile
import json
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .models import ProcessResponse, SilenceSegment
from .processing import process_video, detect_silence, transcribe_to_srt
from . import config as CFG


app = FastAPI(
    title="Subtitle Generation MVP (おまかせ版 v7)",
    description="日本語特化の字幕生成・フィラー削除・無音カットAPI",
    version="7.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=CFG.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静的ファイル配信
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def root():
    """ヘルスチェックエンドポイント"""
    return {
        "message": "Subtitle Generation MVP API (おまかせ版 v7)",
        "status": "running",
        "version": "7.0.0"
    }


@app.get("/config")
def get_config():
    """現行設定を確認"""
    return {
        "ASR_MODEL": CFG.MODEL_NAME,
        "MAX_SIZE_MB": CFG.MAX_SIZE_MB,
        "ALLOWED_EXTS": list(CFG.ALLOWED_EXTS),
        "CORS_ORIGINS": CFG.CORS_ORIGINS or ["*"],
        "CROSSFADE_SEC": CFG.CROSSFADE_SEC,
    }


@app.get("/diag")
def diag():
    """ffmpeg/ffprobe/OPENAI_KEY の有無を確認"""
    import shutil
    return {
        "ffmpeg": shutil.which("ffmpeg") is not None,
        "ffprobe": shutil.which("ffprobe") is not None,
        "openai_key_set": bool(os.getenv("OPENAI_API_KEY"))
    }


@app.get("/demo")
async def demo_page():
    """デモページを表示"""
    demo_html = os.path.join(static_dir, "demo.html")
    if os.path.exists(demo_html):
        return FileResponse(demo_html)
    return {"message": "Demo page not found"}


@app.post("/process", response_model=ProcessResponse)
async def process_subtitle(
    file: UploadFile = File(..., description="処理する動画ファイル"),
    silence_threshold_db: float = Form(default=-35.0, description="無音判定の閾値（dB）"),
    min_silence_sec: float = Form(default=0.35, description="無音と判定する最小秒数"),
    profile: str = Form(default="talk_default", description="使用するプロファイル名")
):
    """
    動画ファイルを処理して字幕と無音区間を生成
    
    Args:
        file: アップロードされた動画ファイル
        silence_threshold_db: 無音判定の閾値（dB）
        min_silence_sec: 無音と判定する最小秒数
        profile: 使用するプロファイル名
        
    Returns:
        ProcessResponse: SRT字幕テキストと無音区間リスト
    """
    # プロファイル読み込み
    filler_words = None
    profile_path = os.path.join(CFG.PROFILE_DIR, f"{profile}.json")
    if os.path.exists(profile_path):
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                profile_data = json.load(f)
                filler_words = profile_data.get("fillers")
                # プロファイルからパラメータを上書き（フォームパラメータが優先）
                if silence_threshold_db == -35.0:  # デフォルト値の場合
                    silence_threshold_db = profile_data.get("silence_threshold_db", -35.0)
                if min_silence_sec == 0.35:  # デフォルト値の場合
                    min_silence_sec = profile_data.get("min_silence_sec", 0.35)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Profile load failed: {e}")
    
    # 一時ファイルに保存
    temp_file = None
    try:
        # ファイルサイズチェック
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)
        if file_size_mb > CFG.MAX_SIZE_MB:
            raise HTTPException(
                status_code=413,
                detail=f"File size ({file_size_mb:.1f}MB) exceeds limit ({CFG.MAX_SIZE_MB}MB)"
            )
        
        # 拡張子チェック
        suffix = os.path.splitext(file.filename)[1].lower() if file.filename else ".mp4"
        if suffix not in CFG.ALLOWED_EXTS:
            raise HTTPException(
                status_code=400,
                detail=f"File extension {suffix} not allowed. Allowed: {CFG.ALLOWED_EXTS}"
            )
        
        # 一時ファイルを作成
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(content)
            tmp_path = temp_file.name
        
        # 無音検出（例外処理強化）
        try:
            silence = detect_silence(tmp_path, silence_threshold_db, min_silence_sec)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"silence detection failed: {e}")
        
        # ASR（例外処理強化）
        try:
            srt, segs = transcribe_to_srt(tmp_path, filler_words)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"ASR failed: {e}")
        
        # レスポンスを構築
        response = ProcessResponse(
            srt_text=srt,
            silence_segments=[
                SilenceSegment(start=seg["start"], end=seg["end"])
                for seg in silence
            ],
            removed_fillers=filler_words
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"処理中にエラーが発生しました: {str(e)}"
        )
    
    finally:
        # 一時ファイルを削除
        if temp_file and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

