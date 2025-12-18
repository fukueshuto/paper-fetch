# PaperFetch

[English](README_EN.md) | [**使い方ガイド**](docs/usage.md) | [インストール](docs/installation.md) | [開発者ガイド](docs/design.md)

**PaperFetch** は、研究者やエンジニアのための、**論文・技術文書の収集と管理を自動化する"Universal Fetcher"** です。

Arxiv、IEEE、3GPPなど、分散している情報源から必要なドキュメントを効率的に検索・ダウンロードし、AI時代に即した形式（Markdown等）へ変換、さらには NotebookLM などのRAGツールへ直接橋渡しをします。

---

## 🚀 なぜ PaperFetch なのか？

- **All-in-One 収集**: 論文(Arxiv/IEEE)も仕様書(3GPP)も、一つのツールで統一的に扱えます。
- **AI Ready**: ダウンロードするだけでなく、PDFを解析しやすいMarkdownに変換したり、NotebookLMへ自動アップロードしてすぐにチャットを開始できる状態にします。
- **Safe & Robust**: サイトごとのレート制限やダウンロード待機時間を適切に管理し、IPブロックのリスクを低減しながら大量の文献を収集できます。
- **Flexible Interfaces**:
    - **Web GUI**: 検索結果を見ながらポチポチ選びたい時に。
    - **CLI**: スクリプトに組み込んで定期実行したい時に。
    - **MCP Server**: Claude などのAIエージェントに調べ物を依頼したい時に。

## 📚 ドキュメント

機能や使い方の詳細は、以下のドキュメントに分割して管理しています。

- **[インストール](docs/installation.md)**: セットアップ手順と前提条件（Python, uv, patchright）。
- **[基本的な使い方](docs/usage.md)**: GUIとCLIの操作方法、検索からダウンロードまでのフロー。
- **[対応データソース](docs/sources.md)**: Arxiv, IEEE, 3GPP, Patentsの詳細仕様。
- **[NotebookLM 連携](docs/notebooklm.md)**: AIノートブックへの自動アップロード機能について。
- **[設定ガイド](docs/configuration.md)**: `config.toml` によるデフォルト設定のカスタマイズ。
- **[トラブルシューティング](docs/troubleshooting.md)**: よくあるエラーと対処法。
- **[アーキテクチャ・開発](docs/design.md)**: 内部構造とコントリビュートのガイド。

## ⚡️ Quick Start

`uv` (Python package manager) を使用するのが最も簡単です。

### 1. インストール

```bash
uv tool install .
# NotebookLM連携用ブラウザの準備
uv run patchright install chromium
```

### 2. GUIを起動

```bash
uv run paper-fetch-gui
```

ブラウザが立ち上がり、すぐに論文検索を始められます。

---

## 🛠 ディレクトリ構成 (出力例)

論文はプロジェクトルート（または設定したパス）の `downloads/` に、検索クエリと日付ごとに整理されて保存されます。

```text
downloads/
└── 20240101_generative_ai/        # {日付}_{クエリ}
    ├── arxiv/
    │   ├── 2312.12345.pdf         # 原本PDF
    │   ├── 2312.12345.md          # 変換されたMarkdownテキスト
    │   └── ...
    ├── notebooklm_session.json    # NotebookLM連携用のセッション情報
    └── ...
```
