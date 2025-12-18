import streamlit as st


from ..config import load_config


def init_session_state():
    # Load default config
    config = load_config()
    core_config = config.get("core", {})
    tgpp_config = config.get("3gpp", {})

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
        st.session_state.source = core_config.get("default_source", "arxiv")
    if "search_limit" not in st.session_state:
        config_limit = core_config.get("search_limit", 10)
        # Handle 0 as Unlimited logic if needed, but for int display usually 0 means 0 or special handling UI side.
        # CLI handles 0 as None. Here we likely keep int.
        st.session_state.search_limit = config_limit
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
        val = core_config.get("download_limit", 10)
        # If config is None (unlimited), handle?
        if val is None:
            val = 10  # Default fallback if None in config for GUI? Or huge number?
        st.session_state.download_limit = val
    if "output_dir" not in st.session_state:
        st.session_state.output_dir = core_config.get("output_dir", "downloads")
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
        st.session_state.convert_to_md = core_config.get("convert_to_md", False)
    if "convert_to_pdf" not in st.session_state:
        st.session_state.convert_to_pdf = tgpp_config.get("convert_to_pdf", True)
    if "save_json" not in st.session_state:
        st.session_state.save_json = True
    if "hits_checked" not in st.session_state:
        st.session_state.hits_checked = False
    if "search_hit_total" not in st.session_state:
        st.session_state.search_hit_total = 0

    if "in_search_phase" not in st.session_state:
        st.session_state.in_search_phase = True
    if "download_method" not in st.session_state:
        st.session_state.download_method = "default"
    if "executed_download_method" not in st.session_state:
        st.session_state.executed_download_method = "default"

    if "cloud_sync_dir" not in st.session_state:
        st.session_state.cloud_sync_dir = ""
    if "last_download_dir" not in st.session_state:
        st.session_state.last_download_dir = None
    if "in_export_mode" not in st.session_state:
        st.session_state.in_export_mode = False
    if "in_session_manager_mode" not in st.session_state:
        st.session_state.in_session_manager_mode = False
    if "notebook_id_env" not in st.session_state:
        st.session_state.notebook_id_env = ""

    # Try to load previous state if this is a fresh run (indicated by empty results/query on startup)
    # However, Streamlit reruns the whole script on interaction, so we need a flag to know if we already loaded.
    if "state_loaded" not in st.session_state:
        load_state()
        st.session_state.state_loaded = True


def save_state():
    """Save critical session state to a pickle file."""
    import pickle

    SESSION_FILE = ".session_state.pkl"

    keys_to_save = [
        "results",
        "query",
        "executed_query",
        "source",
        "executed_source",
        "search_limit",
        "unlimited_search",
        "download_limit",
        "unlimited_download",
        "start_year_input",
        "end_year_input",
        "open_access_only",
        "output_dir",
        "executed_save_dir",
        "downloadable_only",
        "filter_keyword",
        "filter_year_min",
        "filter_year_max",
        "convert_to_md",
        "convert_to_pdf",
        "search_hit_total",
        "in_search_phase",
        "in_session_manager_mode",
        "last_download_dir",
        "cloud_sync_dir",
        "download_method",
        "executed_download_method",
        "notebook_id_env",
    ]

    state_data = {}
    for key in keys_to_save:
        if key in st.session_state:
            state_data[key] = st.session_state[key]

    # Also save selected papers (set of indices)
    if "selected_papers" in st.session_state:
        state_data["selected_papers"] = st.session_state.selected_papers

    try:
        with open(SESSION_FILE, "wb") as f:
            pickle.dump(state_data, f)
    except Exception as e:
        print(f"Failed to save state: {e}")


def load_state():
    """Load session state from pickle file."""
    import pickle

    import os

    SESSION_FILE = ".session_state.pkl"

    if not os.path.exists(SESSION_FILE):
        return

    try:
        with open(SESSION_FILE, "rb") as f:
            state_data = pickle.load(f)

        restricted_keys = [
            "in_search_phase",
            "in_session_manager_mode",
            "in_export_mode",
        ]

        for key, value in state_data.items():
            if key not in restricted_keys:
                st.session_state[key] = value

    except Exception as e:
        print(f"Failed to load state: {e}")
