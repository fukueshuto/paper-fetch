# PaperFetch

PaperFetch is a tool designed to search and download academic paper PDFs from Arxiv and IEEE Xplore. It provides both a Command Line Interface (CLI) and a Model Context Protocol (MCP) server, making it easy to integrate with LLM workflows.

## Features

- **Arxiv Integration**: Search and download papers using the official Arxiv API.
- **IEEE Xplore Integration**: Search and download papers using Playwright (supports Open Access filtering).
- **CLI Tool**: Interactive command-line tool for searching and batch downloading papers.
- **MCP Server**: Exposes `search_papers` and `download_paper` tools for LLM agents.

## Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (recommended for dependency management)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd paper-fetch
    ```

2.  **Install dependencies:**
    ```bash
    uv sync
    ```

3.  **Install Playwright browsers:**
    (Required for IEEE Xplore functionality)
    ```bash
    uv run playwright install
    ```

## Usage

### CLI

You can use the CLI to search and download papers directly from your terminal.

**Search Arxiv:**
```bash
uv run python -m src.cli --source arxiv --query "generative ai" --search-limit 5
```

**Search IEEE Xplore:**
```bash
uv run python -m src.cli --source ieee --query "machine learning" --search-limit 5 --open-access-only
```

**Options:**
- `--source`: `arxiv` or `ieee` (Required)
- `--query`: Search query string (Required)
- `--search-limit`: Maximum number of results to search (Default: Unlimited)
- `--download-limit`: Maximum number of results to download (Default: Unlimited)
- `--output`: Directory to save downloaded PDFs (Default: `downloads`)
- `--downloadable-only`: Filter results to show only downloadable papers
- `--open-access-only`: Search for Open Access papers only (IEEE only)

Follow the interactive prompts to select and download papers.

### MCP Server

To use PaperFetch as an MCP server with an LLM client (e.g., Claude Desktop, VS Code):

**Run the server:**
```bash
uv run python -m src.server
```

**Available Tools:**
- `search_papers(source, query, limit, open_access_only)`: Search for papers.
- `download_paper(url, title, authors, year, save_dir)`: Download a specific paper.

## Project Structure

- `src/cli.py`: CLI entry point.
- `src/server.py`: MCP server entry point.
- `src/fetchers/`: Contains logic for Arxiv and IEEE fetching.
- `downloads/`: Default directory for downloaded PDFs.

## License

[MIT](LICENSE)
