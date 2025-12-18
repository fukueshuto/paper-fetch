# コントリビューションガイド

PaperFetchへの貢献に興味を持っていただきありがとうございます！
このプロジェクトは、研究者やエンジニアが論文を効率的に取得・活用するためのツールを目指しています。

## 開発環境のセットアップ

このプロジェクトでは、Pythonのパッケージ管理に **[uv](https://github.com/astral-sh/uv)** を使用しています。

1. **リポジトリのクローン**
   ```bash
   git clone https://github.com/fukueshuto/paper-fetch.git
   cd paper-fetch
   ```

2. **依存関係のインストール**
   ```bash
   uv sync
   ```
   仮想環境 (`.venv`) が自動的に作成され、必要なパッケージがインストールされます。

3. **ツールの実行確認**
   ```bash
   uv run paper-fetch --help
   ```

## 機能追加について

### 新しいデータソース (Fetcher) の追加

新しい論文ソースを追加したい場合は、`src/paper_fetch/fetchers/` ディレクトリに新しいモジュールを作成してください。

1. `src/paper_fetch/fetchers/base.py` の `BaseFetcher` クラスを継承します。
2. `search()` および `download_pdf()` メソッドを実装します。
3. 取得したデータは `src/paper_fetch/models.py` の `PaperModel` クラスに合わせて正規化してください。

### GUI の修正

GUIは **Streamlit** で構築されています。 `src/paper_fetch/gui.py` がエントリーポイントですが、主要なコンポーネントは `src/paper_fetch/gui_items/` に分割されています。

- `search.py`: 検索フォーム
- `results.py`: 検索結果表示リスト
- `state.py`: Session State管理

## コードスタイルと品質

- コードフォーマッターとして `ruff` の使用を推奨しています。
- プルリクエストを送る前に、基本的な動作確認を行ってください。

## バグ報告・機能要望

GitHub Issues を利用して、バグや機能要望を報告してください。再現手順やエラーログがあると助かります。
特に3GPPや各サイトの構造変更により、スクレイピングが機能しなくなることがあります。気づいた際は報告いただけると幸いです。
