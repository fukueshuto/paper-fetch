import streamlit as st
import os
import sys

# Add src to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from paper_fetch.gui_items.fetcher_info import get_fetcher


def check_hits():
    st.session_state.last_checked_query = st.session_state.query
    st.session_state.last_checked_source = st.session_state.source
    fetcher = get_fetcher(st.session_state.source)
    st.session_state.check_hits_error = None  # Clear previous error

    with st.spinner("Checking hits..."):
        try:
            current_source = st.session_state.source
            current_start_year = (
                int(st.session_state.start_year_input)
                if st.session_state.start_year_input
                and st.session_state.start_year_input.isdigit()
                else None
            )
            current_end_year = (
                int(st.session_state.end_year_input)
                if st.session_state.end_year_input
                and st.session_state.end_year_input.isdigit()
                else None
            )
            current_open_access_only = (
                st.session_state.open_access_only if current_source == "ieee" else False
            )

            if current_source == "ieee":
                total = fetcher.get_total_results(
                    st.session_state.query,
                    start_year=current_start_year,
                    end_year=current_end_year,
                    open_access_only=current_open_access_only,
                )
            else:
                total = fetcher.get_total_results(
                    st.session_state.query,
                    start_year=current_start_year,
                    end_year=current_end_year,
                )

            if total == -1:
                st.session_state.check_hits_error = (
                    "Failed to retrieve hit count from source."
                )
                st.session_state.search_hit_total = 0
            else:
                st.session_state.search_hit_total = total
                st.session_state.hits_checked = True

        except Exception as e:
            st.session_state.check_hits_error = str(e)
            st.session_state.search_hit_total = 0


def search_papers(
    source,
    query,
    limit,
    open_access_only=False,
    sort_by="relevance",
    sort_order="desc",
    start_year=None,
    end_year=None,
):
    fetcher = get_fetcher(source)

    # Progress placeholder for rate limit wait
    progress_placeholder = st.empty()

    def progress_callback(msg):
        if msg:
            progress_placeholder.info(msg)
        else:
            progress_placeholder.empty()

    fetcher.set_progress_callback(progress_callback)

    # Check hits before searching
    check_hits()

    with st.spinner(f"Searching {source.upper()} for '{query}'..."):
        try:
            if source == "ieee":
                results = fetcher.search(
                    query,
                    max_results=limit,
                    open_access_only=open_access_only,
                    sort_by=sort_by,
                    sort_order=sort_order,
                    start_year=start_year,
                    end_year=end_year,
                )
            else:
                results = fetcher.search(
                    query,
                    max_results=limit,
                    sort_by=sort_by,
                    sort_order=sort_order,
                    start_year=start_year,
                    end_year=end_year,
                )
            st.session_state.results = results
            st.session_state.selected_papers = set()  # Reset selection on new search
            # Reset filters on new search
            st.session_state.filter_keyword = ""
            st.session_state.filter_year_min = None
            st.session_state.filter_year_max = None
            return results
        except Exception as e:
            st.error(f"Error during search: {e}")
            return []
        finally:
            progress_placeholder.empty()


def get_default_output_dir(query: str) -> str:
    """Generate default output directory based on date and query."""
    import datetime
    import re

    date_str = datetime.datetime.now().strftime("%Y%m%d")
    # Sanitize query for file path
    safe_query = re.sub(r"[^\w\-_]", "_", query)[:50]
    return os.path.join("downloads", f"{date_str}_{safe_query}")


def download_papers(papers, output_dir_base, source):
    fetcher = get_fetcher(source)

    # Determine final output directory logic
    # If output_dir_base is just "downloads" (default), generate dynamic path
    if output_dir_base == "downloads":
        # We need the query for the path.
        # Assuming st.session_state.query holds the query used for these results.
        query = st.session_state.query
        final_output_dir_base = get_default_output_dir(query)
    else:
        final_output_dir_base = output_dir_base

    # Append source subdirectory
    final_output_dir = os.path.join(final_output_dir_base, source)

    # Calculate total estimate
    min_wait, max_wait = fetcher.get_download_wait_range()
    total_min = min_wait * len(papers)
    total_max = max_wait * len(papers)

    # Progress placeholder for rate limit wait
    progress_placeholder = st.empty()

    def progress_callback(msg):
        if msg:
            progress_placeholder.info(msg)
        else:
            progress_placeholder.empty()

    fetcher.set_progress_callback(progress_callback)

    progress_bar = st.progress(0)
    status_text = st.empty()

    success_count = 0
    total = len(papers)

    st.info(f"Downloading to: {final_output_dir}")
    st.caption(
        f"Estimated total wait time: {total_min/60:.1f} - {total_max/60:.1f} minutes (Rate limit: {min_wait:.1f}-{max_wait:.1f}s/file)"
    )

    for i, paper in enumerate(papers):
        status_text.text(f"Downloading {i+1}/{total}: {paper.title[:50]}...")
        try:
            # fetcher.download_pdf handles the directory creation
            if source == "3gpp":
                # Pass convert_to_md and convert_to_pdf flags
                fetcher.download_pdf(
                    paper,
                    final_output_dir,
                    convert_to_md=st.session_state.convert_to_md,
                    convert_to_pdf=st.session_state.convert_to_pdf,
                )
            else:
                # Arxiv and IEEE now support convert_to_md
                fetcher.download_pdf(
                    paper,
                    final_output_dir,
                    convert_to_md=st.session_state.convert_to_md,
                )
            success_count += 1
        except Exception as e:
            st.error(f"Failed to download '{paper.title}': {e}")

        progress_bar.progress((i + 1) / total)

    status_text.text(f"Completed! Downloaded {success_count}/{total} papers.")
    st.success(f"Downloaded {success_count} papers to {final_output_dir}")
