import streamlit as st


def init_session_state():
    if "results" not in st.session_state:
        st.session_state.results = []
    if "selected_papers" not in st.session_state:
        st.session_state.selected_papers = set()
    if "query" not in st.session_state:
        st.session_state.query = ""
    if "last_checked_query" not in st.session_state:
        st.session_state.last_checked_query = ""
    if "executed_query" not in st.session_state:
        st.session_state.executed_query = ""
    if "last_checked_source" not in st.session_state:
        st.session_state.last_checked_source = "arxiv"
    if "executed_source" not in st.session_state:
        st.session_state.executed_source = "arxiv"
    if "source" not in st.session_state:
        st.session_state.source = "arxiv"
    if "search_limit" not in st.session_state:
        st.session_state.search_limit = 10
    if "unlimited_search" not in st.session_state:
        st.session_state.unlimited_search = True
    if "unlimited_download" not in st.session_state:
        st.session_state.unlimited_download = True
    if "sort_by" not in st.session_state:
        st.session_state.sort_by = "Date"
    if "sort_order" not in st.session_state:
        st.session_state.sort_order = "Desc"
    if "start_year_input" not in st.session_state:
        st.session_state.start_year_input = ""
    if "end_year_input" not in st.session_state:
        st.session_state.end_year_input = ""
    if "open_access_only" not in st.session_state:
        st.session_state.open_access_only = False
    if "download_limit" not in st.session_state:
        st.session_state.download_limit = 10
    if "output_dir" not in st.session_state:
        st.session_state.output_dir = "downloads"
    if "executed_save_dir" not in st.session_state:
        st.session_state.executed_save_dir = "downloads"
    if "downloadable_only" not in st.session_state:
        st.session_state.downloadable_only = True
    if "filter_keyword" not in st.session_state:
        st.session_state.filter_keyword = ""
    if "filter_year_min" not in st.session_state:
        st.session_state.filter_year_min = None
    if "filter_year_max" not in st.session_state:
        st.session_state.filter_year_max = None
    if "convert_to_md" not in st.session_state:
        st.session_state.convert_to_md = False
    if "convert_to_pdf" not in st.session_state:
        st.session_state.convert_to_pdf = True
    if "save_json" not in st.session_state:
        st.session_state.save_json = True
    if "hits_checked" not in st.session_state:
        st.session_state.hits_checked = False
    if "search_hit_total" not in st.session_state:
        st.session_state.search_hit_total = 0

    if "in_search_phase" not in st.session_state:
        st.session_state.in_search_phase = True
