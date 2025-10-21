# 変更履歴 - おまかせ版 v7

## バージョン: v7（おまかせ版）
**リリース日**: 2025年

### 主な変更点

#### 1. プロファイル設定の更新
- **ファイル**: `profiles/talk_default.json`
- **変更内容**: 
  - 視認性重視の字幕スタイル設定（フォントサイズ42、アウトライン3、シャドウ2）
  - フィラーワードを6種類に厳選（えー、あのー、えっと、そのー、まー、えぇと）
  - クロスフェード時間を0.2秒に設定（少し詰める）
  - 正規化ルールの追加（全角スペース→半角、波線の統一）

#### 2. 新APIエンドポイントの追加
- **ファイル**: `app/main.py`
- **追加エンドポイント**:
  - `GET /config`: 現行設定を確認
    - ASRモデル名、最大ファイルサイズ、許可拡張子、CORS設定、クロスフェード時間を返す
  - `GET /diag`: システム診断
    - ffmpeg、ffprobe、OPENAI_API_KEYの有無を確認

#### 3. 例外処理の強化
- **ファイル**: `app/main.py` の `/process` エンドポイント
- **変更内容**:
  - 無音検出失敗時: `HTTPException(status_code=500, detail="silence detection failed: {e}")`
  - ASR失敗時: `HTTPException(status_code=502, detail="ASR failed: {e}")`
  - より詳細なエラーメッセージを提供

#### 4. UIデモの文言最適化
- **ファイル**: `app/static/demo.html`
- **変更内容**:
  - タイトル: 「字幕MVP デモ」→「字幕MVP デモ（おまかせ版）」
  - ボタン: 「処理を実行」→「自動で字幕を作成」
  - 見出し: 
    - 「結果」→「結果（削除フィラー/無音区間）」
    - 「SRT」→「SRTプレビュー（最初の数千文字）」
  - より直感的でユーザーフレンドリーな表現に変更

### 技術的な改善

#### ファイル構成の最適化
```
subtitle-mvp-v7/
├── app/
│   ├── __init__.py
│   ├── config.py          # 設定管理モジュール
│   ├── main.py            # FastAPIアプリ（診断API追加）
│   ├── models.py          # Pydanticモデル
│   ├── processing.py      # コア処理
│   └── static/
│       └── demo.html      # おまかせ版UI
├── cli/
│   └── run_pipeline.py    # CLIツール
├── profiles/
│   └── talk_default.json  # 更新されたプロファイル
├── requirements.txt
├── README.md              # v7対応の説明追加
└── CHANGELOG_v7.md        # このファイル
```

### 使用例

#### 新エンドポイントの使用

```bash
# 設定確認
curl http://127.0.0.1:8000/config
# レスポンス例:
# {
#   "ASR_MODEL": "whisper-1",
#   "MAX_SIZE_MB": 25,
#   "ALLOWED_EXTS": [".mp4", ".mp3", ".wav", ...],
#   "CORS_ORIGINS": ["*"],
#   "CROSSFADE_SEC": 0.2
# }

# システム診断
curl http://127.0.0.1:8000/diag
# レスポンス例:
# {
#   "ffmpeg": true,
#   "ffprobe": true,
#   "openai_key_set": true
# }
```

#### プロファイルを使用した処理

```bash
# API経由
curl -X POST "http://localhost:8000/process" \
  -F "file=@input.mp4" \
  -F "profile=talk_default"

# CLI経由
python cli/run_pipeline.py input.mp4 --profile talk_default
```

### 互換性

- **Python**: 3.11以上推奨
- **FastAPI**: 0.115.0
- **OpenAI API**: 1.51.0
- **FFmpeg**: 4.4以上

### 既知の制限事項

- Whisper APIの制限により、ファイルサイズは25MB以下
- プロファイルは現在1つのみ（talk_default）
- 複数言語対応は未実装

### 次のバージョンでの予定

- [ ] カスタムプロファイルの作成・編集機能
- [ ] バッチ処理API
- [ ] リアルタイム処理進捗通知
- [ ] 複数言語対応

### 差分パッチ適用方法

v6からv7への移行手順：

1. `profiles/talk_default.json` を新しい内容に置き換え
2. `app/main.py` に `/config` と `/diag` エンドポイントを追加
3. `app/main.py` の `/process` 内の例外処理を強化
4. `app/static/demo.html` の文言を「おまかせ版」に変更

### 貢献者

- Manus AI Assistant

### ライセンス

MIT License

