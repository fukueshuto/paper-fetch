# PaperFetch

[English](README_EN.md) | [詳細機能解説](docs/features.md) | [開発者・設計ガイド](docs/design.md) | [トラブルシューティング](docs/troubleshooting.md)

PaperFetchは、Arxiv、IEEE Xplore、3GPPから学術論文や技術仕様書を効率的に検索・ダウンロードするためのツールです。
コマンドラインインターフェース（CLI）、Web GUI、およびModel Context Protocol（MCP）サーバーを提供し、研究者やエンジニアのワークフローを加速します。

## 主な機能

- **マルチソース検索**:
  - **Arxiv**: 公式APIを使用した検索。
  - **IEEE Xplore**: Open Access論文のフィルタリング対応。
  - **3GPP**: 仕様書や寄書の検索、URL指定によるフォルダ一括ダウンロード。
- **特許検索 (USPTO)**:
  - **Status**: ⚠️ **Experimental / Unverified**
  - 現在実装中ですが、APIキー取得待ちのため十分なデバッグが行われていません。動作保証外となります。
- **NotebookLM 連携 (Enhanced)**:
  - ダウンロードした論文PDFをGoogle NotebookLMへ自動アップロード。
  - **Direct Open**: ノートブックIDを指定して既存のノートブックへ直接追加可能。
  - **Session Resume**: 前回作業したノートブック情報を保持し、継続的な追加が可能。
- **高度な設定管理**:
  - `config.toml` によるデフォルト設定の管理。
- **ドキュメント変換**:
  - PDFからMarkdownへのテキスト変換。
  - 3GPPドキュメントのPDF変換オプション。

## 前提条件

- Python 3.12以上
- [uv](https://github.com/astral-sh/uv) （推奨）
- **NotebookLM連携**:
    - `patchright` (自動化用ブラウザ)
    - ※ 初回実行時に自動または手動でブラウザバイナリのインストールが必要です。

## インストール

### 推奨: uv tool

```bash
uv tool install .
# または
uv tool install git+https://github.com/fukueshuto/paper-fetch.git
```

### NotebookLM機能の準備 (Patchright)

NotebookLM連携機能を使用する場合、より検出されにくいブラウザ自動化ツールである `patchright` を使用します。

```bash
# 必要なブラウザバイナリのインストール
uv run patchright install chromium
```

## 使い方

### 1. Web GUIでの使用 (NotebookLM連携)

```bash
uv run paper-fetch-gui
```

GUIの "Export Actions" タブから "NotebookLM" を選択します。
- **Create New Notebook**: 新しいノートブックを作成してアップロード。
- **Add to Existing Notebook**: 既存のノートブックに追加。IDを指定するか、ブラウザ上で手動選択が可能です。

### 2. CLIでの使用

```bash
# 対話モード
paper-fetch

# ワンライナー
paper-fetch --source arxiv --query "generative ai"
```

## ディレクトリ構成

ダウンロードフォルダには、NotebookLMのセッション情報 (`notebooklm_session.json`) も保存され、後から同じノートブックを再利用するのに役立ちます。

```text
downloads/
  └── {YYYYMMDD}_{Query}/
      ├── arxiv/
      ├── notebooklm_session.json  # 自動生成されるセッション情報
      └── ...
```

詳細な仕様は [詳細機能解説](docs/features.md) をご覧ください。
