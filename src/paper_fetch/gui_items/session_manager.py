import streamlit as st
import os
import json
import datetime
from paper_fetch.fetchers.models import Paper
from paper_fetch.gui_items.state import save_state


def session_manager_panel():
    st.markdown(
        '<h1 class="main-header">📂 Session Manager</h1>', unsafe_allow_html=True
    )

    if st.button("⬅️ Back to Search"):
        st.session_state.in_session_manager_mode = False
        st.session_state.in_search_phase = True
        save_state()
        st.rerun()

    st.markdown("---")
    st.subheader("Saved Sessions")
    st.caption(
        "Select a past session to resume work. Sessions are identified by `search_results.json` files in your downloads directory."
    )

    root_dir = "downloads"
    if not os.path.exists(root_dir):
        st.info("No 'downloads' directory found.")
        return

    # Scan for JSON files
    sessions = []

    # Walk depth=2 (root -> query_folder -> json?)
    # Valid structure usually: downloads/YYYYMMDD_query/search_results_*.json
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for f in filenames:
            if f.startswith("search_results_") and f.endswith(".json"):
                full_path = os.path.join(dirpath, f)
                try:
                    stats = os.stat(full_path)
                    mod_time = datetime.datetime.fromtimestamp(stats.st_mtime)

                    # Try to read info for preview
                    with open(full_path, "r", encoding="utf-8") as json_file:
                        data = json.load(json_file)
                        count = len(data)
                        first_paper_source = (
                            data[0].get("source", "Unknown") if count > 0 else "Unknown"
                        )

                    sessions.append(
                        {
                            "path": full_path,
                            "dir": dirpath,
                            "filename": f,
                            "time": mod_time,
                            "count": count,
                            "source": first_paper_source,
                            "parent_folder": os.path.basename(dirpath),
                        }
                    )
                except Exception:
                    pass  # Skip unreadable files

    if not sessions:
        st.info("No saved sessions found.")
        return

    # Sort by time desc
    sessions.sort(key=lambda x: x["time"], reverse=True)

    # Display sessions
    for i, sess in enumerate(sessions):
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2, 3, 1, 1, 1.5])
            with col1:
                st.write(f"**{sess['time'].strftime('%Y-%m-%d %H:%M')}**")
            with col2:
                # Try to infer query from folder name if possible or just show folder
                st.write(f"`{sess['parent_folder']}`")
            with col3:
                st.write(f"{sess['source'].upper()}")
            with col4:
                st.write(f"{sess['count']} papers")
            with col5:
                if st.button("📂 Load", key=f"load_{i}", use_container_width=True):
                    load_session(sess)


def load_session(session_info):
    """Load the session and switch context."""
    json_path = session_info["path"]
    target_dir = session_info["dir"]

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Reconstruct Paper objects
        papers = []
        for p_data in data:
            # Handle date string locally if needed, but Paper model expects date object maybe?
            # The Paper model likely needs to handle string -> date conversion or we do it here.
            # Let's check Paper model. Paper model has Optional[date].
            # We need to parse ISO format string back to date object.
            p_date = None
            if p_data.get("published_date"):
                try:
                    p_date = datetime.date.fromisoformat(p_data["published_date"])
                except ValueError:
                    pass

            paper = Paper(
                source=p_data.get("source", "unknown"),
                id=p_data.get("id", ""),
                title=p_data.get("title", "No Title"),
                authors=p_data.get("authors", []),
                abstract=p_data.get("abstract", ""),
                url=p_data.get("url", ""),
                pdf_url=p_data.get("pdf_url", ""),
                published_date=p_date,
                is_downloadable=p_data.get("is_downloadable", True),
            )
            papers.append(paper)

        # Update Session State
        st.session_state.results = papers
        st.session_state.executed_save_dir = target_dir
        st.session_state.output_dir = target_dir
        st.session_state.executed_source = session_info["source"]

        # Try to infer query from directory name: YYYYMMDD_query
        # 20241218_some_query -> some_query
        parts = session_info["parent_folder"].split("_", 1)
        if len(parts) > 1:
            inferred_query = parts[1]
        else:
            inferred_query = session_info["parent_folder"]

        st.session_state.executed_query = inferred_query
        st.session_state.query = inferred_query

        # Reset selection
        st.session_state.selected_papers = set()

        # Switch Mode
        st.session_state.in_session_manager_mode = False
        st.session_state.in_search_phase = False

        save_state()
        st.success(f"Loaded session from {target_dir}")
        st.rerun()

    except Exception as e:
        st.error(f"Failed to load session: {e}")
