# 開発者・設計ガイド

このドキュメントでは、PaperFetchのアーキテクチャ、コード構造、および拡張を行う開発者向けの情報をまとめます。

## 1. アーキテクチャ概要

PaperFetchは、単一のコアロジック（`src/paper_fetch`）の上に複数のインターフェース（CLI, GUI, MCP）を持つ構成になっています。

```mermaid
graph TD
    User[ユーザー / LLM]
    CLI[CLI (cli.py)]
    GUI[Web GUI (Streamlit)]
    MCP[MCP Server (server.py)]

    Core[Core Logic]
    Fetchers[Fetchers (Data Sources)]
    Converters[Converters (PDF->MD)]
    Config[Configuration System]

    User --> CLI
    User --> GUI
    User --> MCP

    CLI --> Core
    GUI --> Core
    MCP --> Core

    Core --> Fetchers
    Core --> Converters
    Core --> Config
```

## 2. ディレクトリ構造と主要モジュール

```text
src/paper_fetch/
├── cli.py            # CLIのエントリーポイント
├── gui.py            # GUIのエントリーポイント
├── server.py         # MCPサーバーのエントリーポイント (FastMCP)
├── config.py         # 設定読み込みロジック (TOML handling)
├── converter.py      # PDF変換ロジック (Wrapper for external tools)
├── fetchers/         # データソースごとの実装
│   ├── base.py       # Fetcher基底クラス
│   ├── arxiv.py
│   ├── ieee.py
│   └── threegpp.py
├── exporters/        # 外部連携モジュール
│   └── notebooklm.py # NotebookLM連携ロジック (Playwright)
└── gui_items/        # GUIコンポーネント (Streamlit fragments)
    ├── search.py
    ├── results.py
    └── state.py
```

## 3. Class Design: Fetchers

全てのデータソースは `fetchers/base.py` に定義された基底クラスを継承することを推奨しています（現状は完全な強制ではありませんが、共通インターフェースを目指しています）。

### 主なメソッド
- `search(query, **kwargs) -> List[PaperModel]`: 検索を実行し、統一されたデータモデルを返します。
- `download_pdf(paper, save_dir, ...) -> Path`: 指定された論文をダウンロードします。

### データモデル (`models.py`)
- `PaperModel`:
  - `title`: タイトル
  - `authors`: 著者リスト
  - `url`: 論文URL
  - `pdf_url`: PDF直リンク
  - `published_date`: 出版日
  - `is_downloadable`: ダウンロード可否フラグ

## 4. 設定管理フロー

設定は以下の優先順位で適用されます。

1. **CLI引数 / GUI入力**: ユーザーが実行時に指定した値（最優先）。
2. **`config.toml`**: ユーザーディレクトリ等の設定ファイル。
3. **ハードコードされたデフォルト値**: `config.py` 内のフォールバック値。

`config.py` の `load_config()` 関数がこのマージ処理を担当します。

## 5. 開発時の注意点

### GUI (Streamlit) の状態管理
`gui_items/state.py` にて `st.session_state` の初期化を一元管理しています。新しい状態変数を追加する場合は、ここに追加してください。
Streamlitはユーザーの操作ごとにスクリプトを再実行するため、永続化したいデータ（検索結果、選択状態など）は必ず `session_state` に格納する必要があります。

### 外部依存ツールの扱い
PDF変換（marker, pdftotext）やブラウザ操作（playwright）など、外部バイナリシステムに依存する機能については、`shutil.which` などで存在確認を行い、見つからない場合は適切なエラーメッセージまたはフォールバック（変換スキップなど）を提供するように実装してください。

### MCPサーバー
`server.py` は `mcp` ライブラリを使用しています。ここに追加した関数は自動的にLLMから利用可能なツールとして公開されます。APIの変更を行う際は、LLMが理解しやすいdocstringを維持することが重要です。
