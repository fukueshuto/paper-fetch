import streamlit as st


def apply_custom_css():
    st.markdown(
        """
<style>
    .stApp {
        background-color: #f8f9fa;
    }
    .main-header {
        font-family: 'Inter', sans-serif;
        color: #1a1a1a;
        font-weight: 700;
        margin-bottom: 0rem !important;
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
""",
        unsafe_allow_html=True,
    )


def inject_sticky_header_css():
    st.markdown(
        """
        <style>
        div[data-testid="stVerticalBlock"] > div:has(div.sticky-header-marker) {
            position: sticky;
            top: 2.875rem; /* Approximation for Streamlit header height */
            background-color: rgba(248, 249, 250, 0.95);
            z-index: 999;
            padding-top: 0rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid #e5e7eb;
            backdrop-filter: blur(8px);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
