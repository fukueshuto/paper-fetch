import streamlit as st
import os
import sys

# Add src to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paper_fetch.fetchers.arxiv import ArxivFetcher
from paper_fetch.fetchers.ieee import IeeeFetcher

def run_app():
    st.set_page_config(
        page_title="PaperFetch GUI",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Custom CSS for "Premium" feel & Compact Card
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
        .paper-card-compact {
            background-color: white;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            margin-bottom: 0.5rem;
            border-left: 4px solid #4f46e5;
            transition: transform 0.2s;
        }
        .paper-card-compact:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        .paper-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 0.2rem;
            text-decoration: none;
        }
        .paper-meta {
            font-size: 0.85rem;
            color: #64748b;
        }
        .badge {
            display: inline-block;
            padding: 0.2em 0.6em;
            font-size: 0.75em;
            font-weight: 700;
            line-height: 1;
            color: #fff;
            text-align: center;
            white-space: nowrap;
            vertical-align: baseline;
            border-radius: 0.25rem;
            margin-left: 0.5rem;
        }
        .badge-source { background-color: #6c757d; }
        .badge-open { background-color: #28a745; }
        .badge-locked { background-color: #dc3545; }

        /* Sidebar styling adjustment */
        .sidebar-section {
            margin-bottom: 1.5rem;
        }
    </style>
    """, unsafe_allow_html=True)

    # Initialize Session State
    if 'results' not in st.session_state:
        st.session_state.results = []
    if 'selected_papers' not in st.session_state:
        st.session_state.selected_papers = set()
    if 'query' not in st.session_state:
        st.session_state.query = ""
    if 'source' not in st.session_state:
        st.session_state.source = "arxiv"
    if 'search_limit' not in st.session_state:
        st.session_state.search_limit = 10
    if 'unlimited_search' not in st.session_state:
        st.session_state.unlimited_search = False
    if 'sort_by' not in st.session_state:
        st.session_state.sort_by = "relevance"
    if 'sort_order' not in st.session_state:
        st.session_state.sort_order = "desc"
    if 'start_year_input' not in st.session_state:
        st.session_state.start_year_input = ""
    if 'end_year_input' not in st.session_state:
        st.session_state.end_year_input = ""
    if 'open_access_only' not in st.session_state:
        st.session_state.open_access_only = False
    if 'download_limit' not in st.session_state:
        st.session_state.download_limit = 5
    if 'output_dir' not in st.session_state:
        st.session_state.output_dir = "downloads"
    if 'downloadable_only' not in st.session_state:
        st.session_state.downloadable_only = True


    def get_fetcher(source):
        if source == "arxiv":
            return ArxivFetcher()
        elif source == "ieee":
            return IeeeFetcher()
        return None

    def search_papers(source, query, limit, open_access_only=False, sort_by="relevance", sort_order="desc", start_year=None, end_year=None):
        fetcher = get_fetcher(source)
        with st.spinner(f"Searching {source.upper()} for '{query}'..."):
            try:
                if source == "ieee":
                    results = fetcher.search(query, max_results=limit, open_access_only=open_access_only, sort_by=sort_by, sort_order=sort_order, start_year=start_year, end_year=end_year)
                else:
                    results = fetcher.search(query, max_results=limit, sort_by=sort_by, sort_order=sort_order, start_year=start_year, end_year=end_year)
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

    # --- Sidebar: Control Panel ---
    with st.sidebar:
        st.title("PaperFetch")

        # 1. Search Area
        st.markdown("### 🔍 Search")
        # Use session state directly for value to ensure persistence/updates
        query = st.text_input("Query", placeholder="e.g., 'LLM Agents'", value=st.session_state.query, key="query")

        with st.expander("ℹ️ 検索構文のヒント"):
            # Access source from session state as it's defined below in settings
            current_source_for_hint = st.session_state.source
            if current_source_for_hint == "arxiv":
                st.markdown("""
                **Arxiv:**
                - **スペース区切り**: OR (いずれかを含む)
                - **AND検索**: `term1 AND term2`
                - **除外**: `term1 ANDNOT term2`
                - **フィールド**: `ti:`(タイトル), `au:`(著者), `abs:`(要旨)
                """)
            elif current_source_for_hint == "ieee":
                st.markdown("""
                **IEEE:**
                - **スペース区切り**: AND (全てを含む)
                - **OR検索**: `term1 OR term2`
                - **除外**: `term1 NOT term2`
                """)

        col_check, col_search = st.columns(2)
        with col_check:
            check_hits_clicked = st.button("🔢 Check Hits", help="Check number of results")
        with col_search:
            search_clicked = st.button("Go", type="primary", use_container_width=True)

        st.divider()

        st.divider()

        # 3. Settings Area
        with st.expander("⚙️ Settings", expanded=False):
            st.caption("Search Configuration")
            # We use keys to bind to session state.
            # Note: We access st.session_state.source etc. which were initialized.
            source = st.selectbox("Source", ["arxiv", "ieee"], key="source")

            unlimited_search = st.checkbox("Unlimited Search", key="unlimited_search")
            if unlimited_search:
                st.warning("⚠️ Rate limits apply.")
                search_limit = None
            else:
                search_limit = st.number_input("Limit", min_value=1, max_value=100, key="search_limit")

            sort_by = st.selectbox("Sort By", ["relevance", "date"], key="sort_by")
            sort_order = st.selectbox("Sort Order", ["desc", "asc"], key="sort_order")

            col_y1, col_y2 = st.columns(2)
            with col_y1:
                start_year_input = st.text_input("Start", placeholder="YYYY", key="start_year_input")
            with col_y2:
                end_year_input = st.text_input("End", placeholder="YYYY", key="end_year_input")

            start_year = int(start_year_input) if start_year_input and start_year_input.isdigit() else None
            end_year = int(end_year_input) if end_year_input and end_year_input.isdigit() else None

            if source == "ieee":
                open_access_only = st.checkbox("Open Access Only", key="open_access_only")
            else:
                open_access_only = False
                # We don't force reset session state here to avoid infinite rerun loops if not careful,
                # but logically it should be False for Arxiv.
                if 'open_access_only' in st.session_state and st.session_state.open_access_only:
                    st.session_state.open_access_only = False # Ensure it's reset if source changes to arxiv

            st.caption("Download Configuration")
            download_limit = st.number_input("Max Download", min_value=1, max_value=50, key="download_limit")
            output_dir = st.text_input("Save Dir", key="output_dir")
            downloadable_only = st.checkbox("Show Downloadable Only", key="downloadable_only")

    # --- Main Content ---
    st.markdown('<h1 class="main-header">📚 Search Results</h1>', unsafe_allow_html=True)

    # Logic for Search
    if check_hits_clicked and st.session_state.query: # Use st.session_state.query
        fetcher = get_fetcher(st.session_state.source) # Use st.session_state.source
        with st.spinner("Checking hits..."):
            try:
                # Use session state values for search parameters
                current_source = st.session_state.source
                current_start_year = int(st.session_state.start_year_input) if st.session_state.start_year_input and st.session_state.start_year_input.isdigit() else None
                current_end_year = int(st.session_state.end_year_input) if st.session_state.end_year_input and st.session_state.end_year_input.isdigit() else None
                current_open_access_only = st.session_state.open_access_only if current_source == "ieee" else False

                if current_source == "ieee":
                    total = fetcher.get_total_results(st.session_state.query, start_year=current_start_year, end_year=current_end_year, open_access_only=current_open_access_only)
                else:
                    total = fetcher.get_total_results(st.session_state.query, start_year=current_start_year, end_year=current_end_year)

                if total >= 0:
                    st.info(f"Found {total} potential results.")
                else:
                    st.warning("Could not determine hits.")
            except Exception as e:
                st.error(f"Error: {e}")

    if search_clicked and st.session_state.query: # Use st.session_state.query
        # Use session state values for search parameters
        current_source = st.session_state.source
        current_search_limit = st.session_state.search_limit if not st.session_state.unlimited_search else None
        current_open_access_only = st.session_state.open_access_only if current_source == "ieee" else False
        current_sort_by = st.session_state.sort_by
        current_sort_order = st.session_state.sort_order
        current_start_year = int(st.session_state.start_year_input) if st.session_state.start_year_input and st.session_state.start_year_input.isdigit() else None
        current_end_year = int(st.session_state.end_year_input) if st.session_state.end_year_input and st.session_state.end_year_input.isdigit() else None

        search_papers(current_source, st.session_state.query, current_search_limit, current_open_access_only, current_sort_by, current_sort_order, current_start_year, current_end_year)

    # Display Results
    if st.session_state.results:
        results = st.session_state.results

        if st.session_state.downloadable_only: # Use st.session_state.downloadable_only
            display_results = [p for p in results if p.is_downloadable]
        else:
            display_results = results

        # List Control Header
        col_ctrl_1, col_ctrl_2 = st.columns([1, 4])
        with col_ctrl_1:
            # Select All Checkbox
            def toggle_select_all():
                is_checked = st.session_state.select_all_checkbox
                if is_checked:
                    # Select all visible
                    indices = set(range(len(display_results)))
                    st.session_state.selected_papers = indices
                    # Sync individual checkboxes
                    for i in range(len(display_results)):
                        st.session_state[f"chk_{i}"] = True
                else:
                    # Deselect all
                    st.session_state.selected_papers = set()
                    # Sync individual checkboxes
                    for i in range(len(display_results)):
                        st.session_state[f"chk_{i}"] = False

            st.checkbox("Select All", key="select_all_checkbox", on_change=toggle_select_all)

        with col_ctrl_2:
            st.caption(f"Showing {len(display_results)} papers")

        # Render List
        for i, paper in enumerate(display_results):
            # Card Container
            with st.container():
                # Layout: [Checkbox] [Content]
                col_c1, col_c2 = st.columns([0.5, 10])

                with col_c1:
                    # Checkbox for selection
                    # Ensure key exists in session state to avoid KeyErrors on first load if not set
                    chk_key = f"chk_{i}"
                    if chk_key not in st.session_state:
                        st.session_state[chk_key] = i in st.session_state.selected_papers

                    def update_selection(idx=i, key=chk_key):
                        # Update selected_papers based on the widget's new state
                        if st.session_state[key]:
                            st.session_state.selected_papers.add(idx)
                        else:
                            st.session_state.selected_papers.discard(idx)

                    st.checkbox("", key=chk_key, on_change=update_selection, kwargs={'idx': i, 'key': chk_key})

                with col_c2:
                    # Paper Content
                    # Badges
                    badges = f'<span class="badge badge-source">{paper.source.upper()}</span>'
                    if paper.is_downloadable:
                        badges += f' <span class="badge badge-open">Open Access</span>'
                    else:
                        badges += f' <span class="badge badge-locked">Restricted</span>'

                    st.markdown(f"""
                    <div class="paper-card-compact">
                        <div class="paper-title"><a href="{paper.url}" target="_blank">{paper.title}</a> {badges}</div>
                        <div class="paper-meta">
                            👤 {', '.join(paper.authors[:3])}{'...' if len(paper.authors) > 3 else ''} |
                            📅 {paper.published_date.year if paper.published_date else 'Unknown'}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Inline Expander for Abstract
                    with st.expander("📄 Abstract"):
                        st.write(paper.abstract)
                        st.caption(f"PDF URL: {paper.pdf_url}")

    elif search_clicked:
        st.info("No results found.")

    # Footer
    st.markdown("---")
    st.markdown("Built with ❤️ using Streamlit and PaperFetch")

def main():
    import sys
    from streamlit.web import cli as stcli
    sys.argv = ["streamlit", "run", __file__] + sys.argv[1:]
    sys.exit(stcli.main())

if __name__ == "__main__":
    run_app()
