# 字幕生成MVP - Subtitle Generation MVP（おまかせ版 v7）

日本語特化の「字幕生成・フィラー削除・無音カット」を行う半自動編集ツールのMVPです。

## 機能

1. **音声→字幕（Whisper API使用）**: OpenAI Whisper APIを使用して高精度な日本語文字起こし
2. **フィラーワード削除**: 「えー」「あのー」等の日本語フィラーワードを自動削除
3. **無音区間検出**: FFmpegのsilencedetectで無音区間を検出
4. **SRT字幕生成**: 標準的なSRT形式で字幕を出力
5. **FastAPI + CLI**: APIサーバーとコマンドラインツールの両方で利用可能

## 追加（おまかせ版 v7）

- **profiles/talk_default.json をプリセットで更新**（視認性重視/フィラー普通/少し詰める）
- **新エンドポイント**:
  - `GET /config` … 現行設定を確認
  - `GET /diag` … ffmpeg/ffprobe/OPENAI_KEY の有無を確認
- **UIデモの文言をおまかせ版に最適化**
- **例外処理の強化**（無音検出・ASR失敗時の詳細エラー）

### 動作確認例

```bash
# 設定確認
curl http://127.0.0.1:8000/config

# 診断
curl http://127.0.0.1:8000/diag
```

## ディレクトリ構成

```
subtitle-mvp/
  app/
    __init__.py      → パッケージ初期化
    main.py          → FastAPIエントリポイント
    processing.py    → ASR、フィラー削除、無音検出処理
    models.py        → Pydanticモデル
    config.py        → 設定管理
    static/
      demo.html      → デモUI（おまかせ版）
  cli/
    run_pipeline.py  → CLIからの一括実行
  profiles/
    talk_default.json → デフォルトプロファイル
  requirements.txt   → 依存ライブラリ
  README.md          → このファイル
```

## セットアップ

### 1. 依存関係のインストール

```bash
# Pythonパッケージのインストール
pip install -r requirements.txt

# FFmpegのインストール（Ubuntu/Debian）
sudo apt-get update
sudo apt-get install -y ffmpeg

# FFmpegのインストール（macOS）
brew install ffmpeg
```

### 2. 環境変数の設定

OpenAI APIキーを環境変数に設定してください：

```bash
export OPENAI_API_KEY="your-api-key-here"
```

## 使い方

### FastAPI サーバーとして使用

#### サーバーの起動

```bash
cd subtitle-mvp-v7
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

または：

```bash
python -m app.main
```

#### デモUIにアクセス

ブラウザで `http://localhost:8000/demo` にアクセスすると、おまかせ版のデモUIが表示されます。

#### APIエンドポイント

**GET /**
- ヘルスチェック

**GET /config**
- 現行設定を確認

**GET /diag**
- ffmpeg/ffprobe/OPENAI_KEY の有無を確認

**GET /demo**
- デモUIを表示

**POST /process**

動画ファイルをアップロードして字幕と無音区間を生成します。

**リクエスト形式**: `multipart/form-data`

**パラメータ**:
- `file` (required): 動画ファイル
- `silence_threshold_db` (optional, default: -35.0): 無音判定の閾値（dB）
- `min_silence_sec` (optional, default: 0.35): 無音と判定する最小秒数
- `profile` (optional, default: "talk_default"): 使用するプロファイル名

**レスポンス例**:

```json
{
  "srt_text": "1\n00:00:00,000 --> 00:00:05,000\nこんにちは、今日は字幕生成について説明します。\n\n2\n00:00:05,500 --> 00:00:10,000\nこのツールは日本語に特化しています。\n",
  "silence_segments": [
    {"start": 1.23, "end": 2.56},
    {"start": 8.45, "end": 9.12}
  ],
  "removed_fillers": ["えー", "あのー", "えっと", "そのー", "まー", "えぇと"]
}
```

#### curlでのテスト例

```bash
# ヘルスチェック
curl http://localhost:8000/

# 設定確認
curl http://localhost:8000/config

# 診断
curl http://localhost:8000/diag

# 処理実行
curl -X POST "http://localhost:8000/process" \
  -F "file=@input.mp4" \
  -F "silence_threshold_db=-35.0" \
  -F "min_silence_sec=0.35" \
  -F "profile=talk_default"
```

### CLIツールとして使用

#### 基本的な使い方

```bash
python cli/run_pipeline.py input.mp4
```

#### オプション付きの使い方

```bash
python cli/run_pipeline.py input.mp4 --noise -35 --minsil 0.35 --profile talk_default
```

#### ファイルに出力

```bash
python cli/run_pipeline.py input.mp4 \
  --noise -35 \
  --minsil 0.35 \
  --output-srt output.srt \
  --output-json silence.json
```

#### CLIオプション

- `input_file`: 処理する動画ファイルのパス（必須）
- `--noise`: 無音判定の閾値（dB）デフォルト: -35.0
- `--minsil`: 無音と判定する最小秒数 デフォルト: 0.35
- `--profile`: 使用するプロファイル名 デフォルト: talk_default
- `--output-srt`: SRT字幕ファイルの出力先（指定しない場合は標準出力）
- `--output-json`: 無音区間JSONファイルの出力先（指定しない場合は標準出力）

## プロファイル設定

`profiles/talk_default.json` でデフォルトのプロファイル設定を管理しています。

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
  "subtitle_style": {
    "font_family":"Noto Sans JP",
    "font_size":42,
    "outline":3,
    "shadow":2,
    "position":"bottom"
  }
}
```

## フィラーワード辞書

デフォルトプロファイルで対応しているフィラーワード（6種類）:

- えー
- あのー
- えっと
- そのー
- まー
- えぇと

カスタマイズ方法: `profiles/talk_default.json` の `fillers` リストを編集

## 技術スタック

- **FastAPI**: 高速なPython Webフレームワーク
- **OpenAI Whisper API**: 高精度な音声認識
- **FFmpeg**: 動画処理と無音検出
- **Pydantic**: データバリデーション

## 無音検出パラメータの調整

無音検出の精度は以下のパラメータで調整できます：

- **silence_threshold_db**: 小さい値（例: -40dB）にすると、より小さい音も検出します
- **min_silence_sec**: 大きい値にすると、より長い無音のみを検出します

推奨設定：
- 通常の会話: `-35dB`, `0.35秒`
- ノイズが多い環境: `-30dB`, `0.5秒`
- 静かな環境: `-40dB`, `0.25秒`

## 制限事項

- Whisper APIの制限により、ファイルサイズは25MB以下である必要があります
- 長い動画の場合は、事前に分割するか、音声のみを抽出することを推奨します

## 次のステップ（将来の拡張）

- [ ] フィラーワード学習機能
- [ ] カスタムフィラーワード辞書のサポート
- [ ] バッチ処理機能
- [ ] 動画の自動カット機能
- [ ] 複数言語対応

## ライセンス

MIT License

## サポート

問題が発生した場合は、GitHubのIssuesセクションで報告してください。

