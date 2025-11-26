import streamlit as st
import os
import sys
from typing import List

# Add src to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fetchers.arxiv import ArxivFetcher
from src.fetchers.ieee import IeeeFetcher
from src.fetchers.models import Paper

st.set_page_config(
    page_title="PaperFetch GUI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for "Premium" feel
st.markdown("""
<style>
    .stApp {
        background-color: #f8f9fa;
    }
    .main-header {
        font-family: 'Inter', sans-serif;
        color: #1a1a1a;
        font-weight: 700;
    }
    .paper-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
        border-left: 5px solid #4f46e5;
        transition: transform 0.2s;
    }
    .paper-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
    }
    .paper-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 0.5rem;
    }
    .paper-meta {
        font-size: 0.9rem;
        color: #64748b;
        margin-bottom: 0.5rem;
    }
    .paper-abstract {
        font-size: 0.9rem;
        color: #475569;
        line-height: 1.5;
    }
    .stButton button {
        background-color: #4f46e5;
        color: white;
        border-radius: 6px;
        font-weight: 600;
        border: none;
        padding: 0.5rem 1rem;
    }
    .stButton button:hover {
        background-color: #4338ca;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if 'results' not in st.session_state:
    st.session_state.results = []
if 'selected_papers' not in st.session_state:
    st.session_state.selected_papers = set()

def get_fetcher(source):
    if source == "arxiv":
        return ArxivFetcher()
    elif source == "ieee":
        return IeeeFetcher(headless=True)
    return None

def search_papers(source, query, limit, open_access_only=False):
    fetcher = get_fetcher(source)
    with st.spinner(f"Searching {source.upper()} for '{query}'..."):
        try:
            if source == "ieee":
                results = fetcher.search(query, max_results=limit, open_access_only=open_access_only)
            else:
                results = fetcher.search(query, max_results=limit)
            st.session_state.results = results
            st.session_state.selected_papers = set() # Reset selection on new search
            return results
        except Exception as e:
            st.error(f"Error during search: {e}")
            return []

def download_papers(papers, output_dir, source):
    fetcher = get_fetcher(source)
    progress_bar = st.progress(0)
    status_text = st.empty()

    success_count = 0
    total = len(papers)

    for i, paper in enumerate(papers):
        status_text.text(f"Downloading {i+1}/{total}: {paper.title[:50]}...")
        try:
            source_dir = os.path.join(output_dir, source)
            fetcher.download_pdf(paper, source_dir)
            success_count += 1
        except Exception as e:
            st.error(f"Failed to download '{paper.title}': {e}")

        progress_bar.progress((i + 1) / total)

    status_text.text(f"Completed! Downloaded {success_count}/{total} papers.")
    st.success(f"Downloaded {success_count} papers to {os.path.join(output_dir, source)}")

# Sidebar
with st.sidebar:
    st.title("⚙️ Configuration")

    source = st.selectbox("Source", ["arxiv", "ieee"], index=0)

    st.subheader("Search Settings")
    search_limit = st.number_input("Search Limit", min_value=1, max_value=100, value=10)

    if source == "ieee":
        open_access_only = st.checkbox("Open Access Only", value=False)
    else:
        open_access_only = False

    st.subheader("Download Settings")
    download_limit = st.number_input("Download Limit", min_value=1, max_value=50, value=5)
    output_dir = st.text_input("Output Directory", value="downloads")

    downloadable_only = st.checkbox("Show Downloadable Only", value=True)

# Main Content
st.markdown('<h1 class="main-header">📚 PaperFetch GUI</h1>', unsafe_allow_html=True)
st.markdown("Search and download academic papers from Arxiv and IEEE Xplore.")

col1, col2 = st.columns([3, 1])
with col1:
    query = st.text_input("Search Query", placeholder="e.g., 'Large Language Models'")
with col2:
    st.write("") # Spacer
    st.write("")
    search_clicked = st.button("🔍 Search", use_container_width=True)

if search_clicked and query:
    search_papers(source, query, search_limit, open_access_only)

# Display Results
if st.session_state.results:
    results = st.session_state.results

    # Filter display
    if downloadable_only:
        display_results = [p for p in results if p.is_downloadable]
    else:
        display_results = results

    st.markdown(f"### Found {len(display_results)} papers")

    # --- Top Controls ---
    col_top_1, col_top_2, col_top_3 = st.columns([1, 1, 2])

    # Select All Logic
    # We use a callback to update session state for individual checkboxes
    def toggle_select_all():
        select_all_state = st.session_state.select_all_top
        for i in range(len(display_results)):
            st.session_state[f"check_{i}"] = select_all_state

    with col_top_1:
        st.checkbox("Select All", key="select_all_top", on_change=toggle_select_all)

    with col_top_2:
        if st.button("⬇️ Download Selected", key="btn_download_selected_top"):
            selected_indices = []
            for i in range(len(display_results)):
                if st.session_state.get(f"check_{i}", False):
                    selected_indices.append(i)

            if not selected_indices:
                st.warning("Please select at least one paper.")
            else:
                papers_to_download = [display_results[i] for i in selected_indices]
                # Apply download limit
                if len(papers_to_download) > download_limit:
                    st.warning(f"Selection ({len(papers_to_download)}) exceeds limit ({download_limit}). Truncating.")
                    papers_to_download = papers_to_download[:download_limit]
                download_papers(papers_to_download, output_dir, source)

    with col_top_3:
        if st.button("⬇️ Download All (Visible)", key="btn_download_all_top"):
            papers_to_download = display_results
            # Apply download limit
            if len(papers_to_download) > download_limit:
                st.warning(f"Total ({len(papers_to_download)}) exceeds limit ({download_limit}). Truncating.")
                papers_to_download = papers_to_download[:download_limit]
            download_papers(papers_to_download, output_dir, source)

    # --- List ---
    # We remove st.form because it isolates state and makes "Select All" harder without reruns.
    # We use standard widgets.

    for i, paper in enumerate(display_results):
        # Card-like layout
        with st.container():
            col_check, col_content = st.columns([0.05, 0.95])

            with col_check:
                # Initialize key in session state if not present (default False)
                if f"check_{i}" not in st.session_state:
                    st.session_state[f"check_{i}"] = False

                st.checkbox("", key=f"check_{i}")

            with col_content:
                st.markdown(f"""
                <div class="paper-card">
                    <div class="paper-title"><a href="{paper.url}" target="_blank" style="text-decoration:none; color:inherit;">{paper.title}</a></div>
                    <div class="paper-meta">
                        👤 {', '.join(paper.authors[:3])}{'...' if len(paper.authors) > 3 else ''} |
                        📅 {paper.published_date.year if paper.published_date else 'Unknown'} |
                        {'🔓 Open Access' if paper.is_downloadable else '🔒 Restricted'}
                    </div>
                    <div class="paper-abstract">
                        {paper.abstract[:300]}...
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # --- Bottom Controls ---
    st.markdown("---")
    col_btm_1, col_btm_2 = st.columns([1, 3])

    with col_btm_1:
        if st.button("⬇️ Download Selected", key="btn_download_selected_btm"):
            selected_indices = []
            for i in range(len(display_results)):
                if st.session_state.get(f"check_{i}", False):
                    selected_indices.append(i)

            if not selected_indices:
                st.warning("Please select at least one paper.")
            else:
                papers_to_download = [display_results[i] for i in selected_indices]
                if len(papers_to_download) > download_limit:
                    st.warning(f"Selection ({len(papers_to_download)}) exceeds limit ({download_limit}). Truncating.")
                    papers_to_download = papers_to_download[:download_limit]
                download_papers(papers_to_download, output_dir, source)

elif search_clicked:
    st.info("No results found.")

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit and PaperFetch")
