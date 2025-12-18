import streamlit as st
import os
import sys

# Add src to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paper_fetch.gui_items.fetcher_info import get_fetcher, get_search_hint
from paper_fetch.gui_items.operater import (
    check_hits,
    search_papers,
    get_default_output_dir,
)
from paper_fetch.utils import save_papers_to_json
from paper_fetch.gui_items.state import save_state
import datetime


def perform_search():
    """Execute the search logic and update session state."""
    if not st.session_state.query:
        return

    current_source = st.session_state.source
    current_search_limit = (
        st.session_state.search_limit if not st.session_state.unlimited_search else None
    )

    # Calculate initial save directory logic here too, to ensure it's available even if save_json is False
    temp_out_dir = st.session_state.output_dir
    if temp_out_dir == "downloads":
        st.session_state.executed_save_dir = get_default_output_dir(
            st.session_state.query
        )
    else:
        st.session_state.executed_save_dir = temp_out_dir

    current_open_access_only = (
        st.session_state.open_access_only if current_source == "ieee" else False
    )
    current_sort_by = st.session_state.sort_by
    current_sort_order = st.session_state.sort_order
    current_start_year = (
        int(st.session_state.start_year_input)
        if st.session_state.start_year_input
        and st.session_state.start_year_input.isdigit()
        else None
    )
    current_end_year = (
        int(st.session_state.end_year_input)
        if st.session_state.end_year_input and st.session_state.end_year_input.isdigit()
        else None
    )

    search_papers(
        current_source,
        st.session_state.query,
        current_search_limit,
        current_open_access_only,
        current_sort_by,
        current_sort_order,
        current_start_year,
        current_end_year,
    )

    # Auto-save if flag is set
    if st.session_state.save_json and st.session_state.results:
        out_dir = st.session_state.output_dir
        if out_dir == "downloads":
            save_dir = get_default_output_dir(st.session_state.query)
        else:
            save_dir = out_dir

        # Save calculated path to session state for display in results screen
        st.session_state.executed_save_dir = save_dir
        # Update output_dir to reflect the actual save location if it was default
        if out_dir == "downloads":
            st.session_state.output_dir = save_dir

        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"search_results_{timestamp}.json"
        save_path = os.path.join(save_dir, filename)

        try:
            save_papers_to_json(st.session_state.results, save_path)
            st.success(f"Saved results to {save_path}")
        except Exception as e:
            st.error(f"Failed to save results: {e}")


def search_panel():
    st.markdown('<h1 class="main-header">📚 Paper Fetch</h1>', unsafe_allow_html=True)

    # 1. Search Form (Query & Search Button only)
    # with st.form("search_form"):
    # Helper to sync widget state to persistent state
    def sync_widget(key):
        st.session_state[key] = st.session_state[f"widget_{key}"]
        save_state()

    # 1. Search Form (Query & Search Button only)
    # with st.form("search_form"):
    with st.container(border=True):
        col_source, col_query = st.columns([1, 4], vertical_alignment="bottom")
        with col_source:
            st.session_state.source = st.selectbox(
                "source",
                ["arxiv", "ieee", "3gpp", "uspto"],
                index=["arxiv", "ieee", "3gpp", "uspto"].index(st.session_state.source),
                key="widget_source",
                on_change=sync_widget,
                kwargs={"key": "source"},
            )
        with col_query:
            # エンターを押すなりinputbox外をクリックするとqueryが更新されてon_change扱いになるらしい
            st.text_input(
                "Query",
                placeholder="e.g., 'LLM Agents' or URL",
                value=st.session_state.query,
                key="widget_query",
                on_change=sync_widget,
                kwargs={"key": "query"},
            )

        # Dynamic Download Method Selector
        fetcher_instance = get_fetcher(st.session_state.source)  # Use persistent source
        if fetcher_instance and fetcher_instance.supports_download_methods:
            # Determine index safely
            current_method = st.session_state.download_method
            options = fetcher_instance.available_download_methods
            idx = options.index(current_method) if current_method in options else 0

            st.selectbox(
                "Download Method",
                options,
                index=idx,
                key="widget_download_method",
                on_change=sync_widget,
                kwargs={"key": "download_method"},
            )

        # Search Hints
        with st.expander("ℹ️ 検索構文のヒント"):
            current_source_for_hint = st.session_state.source
            st.markdown(get_search_hint(current_source_for_hint))

        col_search_btns, col_save_json = st.columns([2, 1])
        with col_search_btns:
            col_check, col_exec = st.columns([1, 1])
            with col_check:
                # Check Hits Button (First button = Default for Enter key)
                check_clicked = st.button(
                    "❓ Check Hits",
                    type="secondary",
                    # disabled=st.session_state.hits_checked,
                    use_container_width=True,
                )
            with col_exec:
                # Search Button (Submit)
                if st.session_state.save_json:
                    search_button_label = "🔎 Search & Save JSON"
                else:
                    search_button_label = "🔎 Search"

                search_clicked = st.button(
                    search_button_label,
                    type="primary",
                    # disabled=not st.session_state.hits_checked,
                    use_container_width=True,
                )

        with col_save_json:
            st.checkbox(
                "Save Results to JSON",
                value=st.session_state.save_json,
                key="widget_save_json",
                help="Automatically save search results to a JSON file after searching.",
                on_change=sync_widget,
                kwargs={"key": "save_json"},
            )
            # Session Manager Button
            if st.button("📂 Session Manager", use_container_width=True):
                st.session_state.in_session_manager_mode = True
                save_state()
                st.rerun()

        if search_clicked:
            st.session_state.last_checked_query = st.session_state.query
            st.session_state.executed_query = st.session_state.query
            st.session_state.executed_source = st.session_state.source
            # Save the download method used for this search
            if "download_method" in st.session_state:
                st.session_state.executed_download_method = (
                    st.session_state.download_method
                )
            else:
                st.session_state.executed_download_method = "default"

            perform_search()
            st.session_state.in_search_phase = False

            save_state()  # Ensure executed state is saved
            st.rerun()

        # Hit Count Check Logic
        if (
            st.session_state.last_checked_query != st.session_state.query
            or st.session_state.last_checked_source != st.session_state.source
            or check_clicked
        ) and st.session_state.query != "":
            check_hits()
            st.rerun()

        if "check_hits_error" in st.session_state and st.session_state.check_hits_error:
            st.error(f"Error checking hits: {st.session_state.check_hits_error}")
        elif st.session_state.hits_checked:
            if st.session_state.search_hit_total > 0:
                s_min, s_max = get_fetcher(
                    st.session_state.source
                ).get_search_wait_range()
                st.info(
                    f"🔎 Found {st.session_state.search_hit_total} potential results.️ ⏳️ Estimated wait time: {st.session_state.search_hit_total * s_min:.1f}s - {st.session_state.search_hit_total * s_max:.1f}s ({s_min:.1f}s - {s_max:.1f}s per result)"
                )

            else:
                st.warning("Could not determine hits (0 returned).")
        else:
            st.warning(
                "⚠️ 過負荷を避けるため、検索前にヒット数を確認してください (Enter or 'Check Hits' button)"
            )

        col_sort_by, col_sort_order, col_year_start, col_year_end = st.columns(4)
        with col_sort_by:
            st.selectbox(
                "Sort By",
                ["Relevance", "Date"],
                index=["Relevance", "Date"].index(st.session_state.sort_by),
                key="widget_sort_by",
                on_change=sync_widget,
                kwargs={"key": "sort_by"},
            )
        with col_sort_order:
            st.selectbox(
                "Sort Order",
                ["Desc", "Asc"],
                index=["Desc", "Asc"].index(st.session_state.sort_order),
                key="widget_sort_order",
                on_change=sync_widget,
                kwargs={"key": "sort_order"},
            )
        with col_year_start:
            st.text_input(
                "Start Year",
                placeholder="YYYY",
                value=st.session_state.start_year_input,
                key="widget_start_year_input",
                on_change=sync_widget,
                kwargs={"key": "start_year_input"},
            )
        with col_year_end:
            st.text_input(
                "End Year",
                placeholder="YYYY",
                value=st.session_state.end_year_input,
                key="widget_end_year_input",
                on_change=sync_widget,
                kwargs={"key": "end_year_input"},
            )

        if st.session_state.source == "ieee":
            st.checkbox(
                "Open Access Only",
                value=st.session_state.open_access_only,
                key="widget_open_access_only",
                on_change=sync_widget,
                kwargs={"key": "open_access_only"},
            )

        col_limit, col_unlimited_search = st.columns(2, vertical_alignment="bottom")
        with col_limit:
            if st.session_state.unlimited_search:
                st.warning("⚠️ Unlimited Search is active. Potential ban risk.")
            else:
                st.number_input(
                    "Limit",
                    min_value=1,
                    max_value=None,
                    value=st.session_state.search_limit,
                    key="widget_search_limit",
                    disabled=st.session_state.unlimited_search,
                    on_change=sync_widget,
                    kwargs={"key": "search_limit"},
                )
        with col_unlimited_search:
            st.checkbox(
                "Unlimited Search",
                value=st.session_state.unlimited_search,
                key="widget_unlimited_search",
                on_change=sync_widget,
                kwargs={"key": "unlimited_search"},
            )
