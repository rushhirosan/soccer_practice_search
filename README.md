# YouTube チャンネル動画検索サイト

このプロジェクトは、特定の YouTube チャンネルのサッカー関係の動画を取得し、ウェブサイト上で検索・閲覧できるアプリケーションです。ユーザーはキーワードや選択肢で動画を検索し、詳細情報を閲覧することができます。

## 概要

- **機能**:
  - 特定の YouTube チャンネルから動画情報を取得
  - 動画タイトル、説明、公開日、再生回数などの詳細情報を表示
  - 検索バーを用いた動画のキーワード検索
  - 動画のサムネイル画像の表示
  - 動画ページへのリンク提供

## 必要な環境

- Python 3.8 以上
- Flask
- google-api-python-client
- その他必要なパッケージは `requirements.txt` を参照してください。

## インストール手順

1. **リポジトリのクローン**

   ```bash
   git clone https://github.com/yourusername/soccer-content-search.git
   cd soccer-content-search