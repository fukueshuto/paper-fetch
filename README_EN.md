# PaperFetch

PaperFetch is a tool designed to search and download academic paper PDFs from Arxiv and IEEE Xplore. It provides both a Command Line Interface (CLI) and a Model Context Protocol (MCP) server, making it easy to integrate with LLM workflows.

## Features

- **Arxiv Integration**: Search and download papers using the official Arxiv API.
- **IEEE Xplore Integration**: Search and download papers using internal REST API (supports Open Access filtering).
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

## Usage

### CLI

You can use the CLI to search and download papers directly from your terminal.

**Search Arxiv:**
```bash
uv run paper-fetch --source arxiv --query "generative ai" --search-limit 5
```

**Search IEEE Xplore:**
```bash
uv run paper-fetch --source ieee --query "machine learning" --search-limit 5 --open-access-only
```

**Options:**
- `--source`: `arxiv` or `ieee` (Required)
- `--query`: Search query string (Required)
- `--search-limit`: Maximum number of results to search (Default: 10, `0` for unlimited)
- `--download-limit`: Maximum number of results to download (Default: Unlimited)
- `--output`: Directory to save downloaded PDFs (Default: `downloads`)
- `--downloadable-only`: Filter results to show only downloadable papers
- `--open-access-only`: Search for Open Access papers only (IEEE only)
- `--sort-by`: Sort criterion (`relevance` or `date`, Default: `relevance`)
- `--sort-order`: Sort order (`desc` or `asc`, Default: `desc`)
- `--start-year`: Filter by start year (e.g., 2020)
- `--end-year`: Filter by end year (e.g., 2024)
- `--export`: Export search results to a JSON file (e.g., `results.json`)
- `--from-file`: Download papers from a JSON file (e.g., `results.json`)

Follow the interactive prompts to select and download papers.

### Output

Downloaded papers are saved in source-specific subdirectories within the specified output directory (Default: `downloads`).

**Directory Structure:**
```
downloads/
  ├── arxiv/
  │   └── 2024_11_arxiv_Smith_Doe_Generative_AI.pdf
  └── ieee/
      └── 2023_05_ieee_Johnson_Deep_Learning.pdf
```

**Filename Format:**
`{Year}_{Month}_{Source}_{FirstAuthor}_{LastAuthor}_{Title}.pdf`
(LastAuthor is omitted if there is only one author)

### Web GUI

You can use the browser-based GUI for a more intuitive search and download experience.

**Run the GUI:**
```bash
uv run paper-fetch-gui
```
The browser will open automatically at `http://localhost:8501`.

### MCP Server

To use PaperFetch as an MCP server with an LLM client (e.g., Claude Desktop, VS Code):

**Run the server:**
```bash
uv run paper-fetch-mcp
```

**Available Tools:**
- `search_papers(source, query, limit, open_access_only)`: Search for papers.
- `download_paper(url, title, authors, year, save_dir)`: Download a specific paper.

## Project Structure

- `src/paper_fetch/cli.py`: CLI entry point.
- `src/paper_fetch/server.py`: MCP server entry point.
- `src/paper_fetch/fetchers/`: Contains logic for Arxiv and IEEE fetching.
- `downloads/`: Default directory for downloaded PDFs.
