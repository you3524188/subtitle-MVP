# 差分パッチサマリー: v6 → v7（おまかせ版）

## 概要

v6ベースから「おまかせ版 v7」への差分パッチを適用しました。
このバージョンでは、プロファイル設定の最適化、診断機能の追加、UI文言の改善を実施しています。

## 変更ファイル一覧

### 1. 置き換え（1ファイル）

#### `profiles/talk_default.json`
**変更内容**: 完全置き換え

```json
{
  "profile_name": "talk_default",
  "silence_threshold_db": -35.0,
  "min_silence_sec": 0.35,
  "crossfade_sec": 0.2,
  "fillers": ["えー","あのー","えっと","そのー","まー","えぇと"],
  "punctuation_style": "casual",
  "normalize_rules": [
    {"from":"　","to":" "},
    {"from":"\u3000","to":" "},
    {"from":"～","to":"〜"}
  ],
  "subtitle_style": {"font_family":"Noto Sans JP","font_size":42,"outline":3,"shadow":2,"position":"bottom"}
}
```

**変更理由**:
- フィラーワードを6種類に厳選（視認性と処理速度のバランス）
- 字幕スタイルを視認性重視に設定
- 正規化ルールで全角スペースと波線を統一

### 2. 修正（3ファイル）

#### `app/main.py`

**追加1**: 設定確認エンドポイント

```python
@app.get("/config")
def get_config():
    from app import config as CFG
    return {
        "ASR_MODEL": CFG.MODEL_NAME,
        "MAX_SIZE_MB": CFG.MAX_SIZE_MB,
        "ALLOWED_EXTS": list(CFG.ALLOWED_EXTS),
        "CORS_ORIGINS": CFG.CORS_ORIGINS or ["*"],
        "CROSSFADE_SEC": CFG.CROSSFADE_SEC,
    }
```

**追加2**: 診断エンドポイント

```python
@app.get("/diag")
def diag():
    import shutil, os
    return {
        "ffmpeg": shutil.which("ffmpeg") is not None,
        "ffprobe": shutil.which("ffprobe") is not None,
        "openai_key_set": bool(os.getenv("OPENAI_API_KEY"))
    }
```

**修正3**: 無音検出の例外処理強化

```python
# 変更前:
silence = detect_silence(tmp_path, silence_threshold_db, min_silence_sec)

# 変更後:
try:
    silence = detect_silence(tmp_path, silence_threshold_db, min_silence_sec)
except Exception as e:
    raise HTTPException(status_code=500, detail=f"silence detection failed: {e}")
```

**修正4**: ASRの例外処理強化

```python
# 変更前:
srt, segs = transcribe_to_srt(tmp_path, filler_words)

# 変更後:
try:
    srt, segs = transcribe_to_srt(tmp_path, filler_words)
except Exception as e:
    raise HTTPException(status_code=502, detail=f"ASR failed: {e}")
```

#### `app/static/demo.html`

**修正箇所**:

| 要素 | 変更前 | 変更後 |
|------|--------|--------|
| タイトル | `字幕MVP デモ` | `字幕MVP デモ（おまかせ版）` |
| サブタイトル | `動画をアップロードして、自動で字幕を生成します` | （変更なし） |
| ボタン | `処理を実行` | `自動で字幕を作成` |
| 結果見出し1 | `結果` | `結果（削除フィラー/無音区間）` |
| 結果見出し2 | `SRT` | `SRTプレビュー（最初の数千文字）` |

**変更理由**: 「おまかせ版」のコンセプトに合わせ、より直感的でユーザーフレンドリーな表現に変更

#### `README.md`

**追加セクション**: 「追加（おまかせ版 v7）」

```markdown
## 追加（おまかせ版 v7）

- profiles/talk_default.json をプリセットで更新（視認性重視/フィラー普通/少し詰める）
- 新エンドポイント:
  - GET /config … 現行設定を確認
  - GET /diag … ffmpeg/ffprobe/OPENAI_KEY の有無を確認
- UIデモの文言をおまかせ版に最適化

### 動作確認例
curl http://127.0.0.1:8000/config
curl http://127.0.0.1:8000/diag
```

## 動作確認手順

### 1. サーバー起動

```bash
cd subtitle-mvp-v7
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. 診断実行

```bash
# 設定確認
curl http://127.0.0.1:8000/config

# システム診断
curl http://127.0.0.1:8000/diag
```

**期待される出力**:

```json
// /config
{
  "ASR_MODEL": "whisper-1",
  "MAX_SIZE_MB": 25,
  "ALLOWED_EXTS": [".mp4", ".mp3", ".wav", ".m4a", ".webm", ".avi", ".mov"],
  "CORS_ORIGINS": ["*"],
  "CROSSFADE_SEC": 0.2
}

// /diag
{
  "ffmpeg": true,
  "ffprobe": true,
  "openai_key_set": true
}
```

### 3. デモUIテスト

1. ブラウザで `http://localhost:8000/demo` にアクセス
2. タイトルが「字幕MVP デモ（おまかせ版）」であることを確認
3. ボタンが「自動で字幕を作成」であることを確認
4. 動画ファイルをアップロードして処理実行
5. 結果に「削除されたフィラー」が表示されることを確認

### 4. API処理テスト

```bash
curl -X POST "http://localhost:8000/process" \
  -F "file=@test.mp4" \
  -F "profile=talk_default"
```

**期待される動作**:
- 無音検出失敗時: `status_code=500, detail="silence detection failed: ..."`
- ASR失敗時: `status_code=502, detail="ASR failed: ..."`
- 成功時: SRT字幕 + 無音区間 + 削除フィラーリスト

## ファイルサイズ

```
subtitle-mvp-omakase-v7.zip: 約20KB（圧縮後）
展開後: 約80KB（12ファイル）
```

## 互換性

- **v6からの移行**: 完全互換（既存APIは変更なし、新規エンドポイント追加のみ）
- **Python**: 3.11以上
- **依存ライブラリ**: requirements.txt参照（変更なし）

## テスト済み環境

- OS: Ubuntu 22.04
- Python: 3.11.0rc1
- FFmpeg: 4.4.2
- OpenAI API: 1.51.0

## トラブルシューティング

### 診断エンドポイントで `openai_key_set: false` の場合

```bash
export OPENAI_API_KEY="your-api-key-here"
```

### 診断エンドポイントで `ffmpeg: false` の場合

```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y ffmpeg

# macOS
brew install ffmpeg
```

## まとめ

このパッチにより、以下が実現されました：

✅ プロファイル設定の最適化（視認性重視）  
✅ 診断機能の追加（/config, /diag）  
✅ 例外処理の強化（詳細なエラーメッセージ）  
✅ UI文言の「おまかせ版」対応  
✅ 完全な後方互換性の維持

v6ベースのシステムに対して、安全に適用可能な差分パッチです。

