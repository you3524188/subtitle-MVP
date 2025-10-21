#!/usr/bin/env python3
"""
CLI tool for subtitle generation pipeline
Usage: python cli/run_pipeline.py input.mp4 --noise -35 --minsil 0.35
"""
import sys
import os
import json
import argparse

# 親ディレクトリをパスに追加してappモジュールをインポート可能にする
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.processing import process_video


def main():
    """CLIメイン関数"""
    parser = argparse.ArgumentParser(
        description="日本語特化の字幕生成・フィラー削除・無音カットCLIツール（おまかせ版 v7）"
    )
    
    parser.add_argument(
        "input_file",
        help="処理する動画ファイルのパス"
    )
    
    parser.add_argument(
        "--noise",
        type=float,
        default=-35.0,
        help="無音判定の閾値（dB）デフォルト: -35.0"
    )
    
    parser.add_argument(
        "--minsil",
        type=float,
        default=0.35,
        help="無音と判定する最小秒数 デフォルト: 0.35"
    )
    
    parser.add_argument(
        "--output-srt",
        help="SRT字幕ファイルの出力先（指定しない場合は標準出力）"
    )
    
    parser.add_argument(
        "--output-json",
        help="無音区間JSONファイルの出力先（指定しない場合は標準出力）"
    )
    
    parser.add_argument(
        "--profile",
        default="talk_default",
        help="使用するプロファイル名 デフォルト: talk_default"
    )
    
    args = parser.parse_args()
    
    # 入力ファイルの存在確認
    if not os.path.exists(args.input_file):
        print(f"エラー: 入力ファイルが見つかりません: {args.input_file}", file=sys.stderr)
        sys.exit(1)
    
    # プロファイル読み込み
    filler_words = None
    profile_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "profiles")
    profile_path = os.path.join(profile_dir, f"{args.profile}.json")
    if os.path.exists(profile_path):
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                profile_data = json.load(f)
                filler_words = profile_data.get("fillers")
                print(f"プロファイル読み込み: {args.profile}", file=sys.stderr)
                print(f"フィラーワード: {filler_words}", file=sys.stderr)
        except Exception as e:
            print(f"警告: プロファイル読み込み失敗: {e}", file=sys.stderr)
    
    try:
        print(f"処理中: {args.input_file}", file=sys.stderr)
        print(f"無音閾値: {args.noise}dB, 最小無音時間: {args.minsil}秒", file=sys.stderr)
        
        # 動画を処理
        srt_text, silence_segments = process_video(
            args.input_file,
            args.noise,
            args.minsil,
            filler_words
        )
        
        # SRT字幕を出力
        if args.output_srt:
            with open(args.output_srt, 'w', encoding='utf-8') as f:
                f.write(srt_text)
            print(f"\nSRT字幕を保存しました: {args.output_srt}", file=sys.stderr)
        else:
            print("\n=== SRT字幕 ===", file=sys.stderr)
            print(srt_text)
        
        # 無音区間を出力
        silence_json = json.dumps(silence_segments, indent=2, ensure_ascii=False)
        
        if args.output_json:
            with open(args.output_json, 'w', encoding='utf-8') as f:
                f.write(silence_json)
            print(f"\n無音区間を保存しました: {args.output_json}", file=sys.stderr)
        else:
            print("\n=== 無音区間 ===", file=sys.stderr)
            print(silence_json)
        
        print("\n処理が完了しました！", file=sys.stderr)
        
    except Exception as e:
        print(f"\nエラー: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

