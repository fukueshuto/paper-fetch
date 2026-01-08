import streamlit as st
import os
import sys

# Add src to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paper_fetch.gui_items.style import apply_custom_css
from paper_fetch.gui_items.state import init_session_state
from paper_fetch.gui_items.search import search_panel
from paper_fetch.gui_items.results import results_panel
from paper_fetch.gui_items.session_manager import session_manager_panel


def main():
    import sys
    from streamlit.web import cli as stcli

    sys.argv = ["streamlit", "run", __file__]
    sys.exit(stcli.main())


if __name__ == "__main__":
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
    st.set_page_config(
        page_title="PaperFetch GUI",
        page_icon=icon_path,
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Apply Custom CSS
    apply_custom_css()

    # Initialize Session State
    init_session_state()

    # --- Main Content ---

    # --- Search Panel Container ---
    if st.session_state.in_session_manager_mode:
        session_manager_panel()
    elif st.session_state.in_search_phase:
        search_panel()
    else:
        results_panel()

    # Footer
    st.markdown("---")
    st.markdown("Built with ❤️ using Streamlit and PaperFetch")
