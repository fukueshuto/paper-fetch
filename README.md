# PaperFetch

PaperFetchは、ArxivおよびIEEE Xploreから学術論文のPDFを検索・ダウンロードするためのツールです。コマンドラインインターフェース（CLI）とModel Context Protocol（MCP）サーバーの両方を提供しており、LLMワークフローへの統合が容易です。

## 機能

- **Arxiv連携**: 公式Arxiv APIを使用して論文を検索・ダウンロードします。
- **IEEE Xplore連携**: Playwrightを使用して論文を検索・ダウンロードします（Open Accessフィルタリング対応）。
- **CLIツール**: 論文の検索と一括ダウンロードを行うための対話型コマンドラインツールです。
- **MCPサーバー**: LLMエージェント向けに `search_papers` および `download_paper` ツールを公開します。

## 前提条件

- Python 3.13以上
- [uv](https://github.com/astral-sh/uv) （依存関係管理に推奨）

## インストール

1.  **リポジトリのクローン:**
    ```bash
    git clone <repository-url>
    cd paper-fetch
    ```

2.  **依存関係のインストール:**
    ```bash
    uv sync
    ```

3.  **Playwrightブラウザのインストール:**
    （IEEE Xplore機能に必要です）
    ```bash
    uv run playwright install
    ```

## 使い方

### CLI

ターミナルから直接論文を検索・ダウンロードできます。

**Arxivの検索:**
```bash
uv run python -m src.cli --source arxiv --query "generative ai" --search-limit 5
```

**IEEE Xploreの検索:**
```bash
uv run python -m src.cli --source ieee --query "machine learning" --search-limit 5 --open-access-only
```

**オプション:**
- `--source`: `arxiv` または `ieee` （必須）
- `--query`: 検索クエリ文字列 （必須）
- `--search-limit`: 検索する最大結果数 （デフォルト: 無制限）
- `--download-limit`: ダウンロードする最大結果数 （デフォルト: 無制限）
- `--output`: PDF保存先ディレクトリ （デフォルト: `downloads`）
- `--downloadable-only`: ダウンロード可能な論文のみを表示
- `--open-access-only`: Open Access論文のみを検索（IEEEのみ）

対話プロンプトに従って、論文を選択・ダウンロードしてください。

### MCPサーバー

LLMクライアント（Claude Desktop, VS Codeなど）でPaperFetchをMCPサーバーとして使用する場合：

**サーバーの起動:**
```bash
uv run python -m src.server
```

**利用可能なツール:**
- `search_papers(source, query, limit, open_access_only)`: 論文を検索します。
- `download_paper(url, title, authors, year, save_dir)`: 特定の論文をダウンロードします。

## プロジェクト構成

- `src/cli.py`: CLIのエントリーポイント
- `src/server.py`: MCPサーバーのエントリーポイント
- `src/fetchers/`: ArxivおよびIEEEの取得ロジック
- `downloads/`: ダウンロードされたPDFのデフォルト保存先

## ライセンス

[MIT](LICENSE)
