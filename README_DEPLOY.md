# Online Deploy Pack (v7, おまかせ版)

このフォルダは、`subtitle-mvp-omakase-v7.zip` をオンラインで公開するための最短セットです。

## 0) 前提
- すでに `subtitle-mvp-omakase-v7.zip` が手元にあること
- unzip したフォルダ直下に、この「deploy pack」のファイルをコピーしてください
  （`Dockerfile` と `requirements.txt` が同じ階層にある状態）

## 1) Render.com（いちばん簡単）
1. リポジトリを作る（GitHubなどにアップ）
2. Renderにログイン → New + → Web Service → "Use Docker" を選択
3. `render.yaml` を使うか、ダッシュボードから `OPENAI_API_KEY` を環境変数に設定
4. デプロイ後、`/diag`, `/config`, `/ui/demo.html` で確認

## 2) Railway（Docker）
- このフォルダを含む状態で Railway にプロジェクト作成 → Deploy from repo
- 環境変数 `OPENAI_API_KEY` を設定 → デプロイ
- Health: `/health`

## 3) Google Cloud Run（本番運用向け）
```
bash cloudrun_deploy.sh <GCP_PROJECT_ID> <SERVICE_NAME>
```
- 事前に `gcloud` のログインとプロジェクト作成が必要です
- デプロイ後、表示されたURLで `/diag` → `/config` を確認

## 4) 環境変数
- `OPENAI_API_KEY`（必須）
- `CORS_ORIGINS`（例: `https://yourapp.com`）
- `ASR_MODEL`（既定: whisper-1）
- `CROSSFADE_SEC`（既定: 0.2）

## 5) よくあるハマり
- ffmpeg が無い → このDockerfileには同梱済み
- CORSでUIから叩けない → `CORS_ORIGINS` を正しいドメインに設定
- タイムアウト → プラットフォームのリクエスト上限に注意（必要ならジョブ化）

## 6) 動作確認
- `/health` `/diag` `/config` が通る → OK
- `/ui/demo.html` が表示 → OK
- `/process` が動作 → Whisperの課金・API制限に留意