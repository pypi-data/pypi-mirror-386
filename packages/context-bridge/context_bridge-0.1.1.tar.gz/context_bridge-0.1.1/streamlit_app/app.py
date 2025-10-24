"""
Context Bridge - Streamlit UI

Main entry point for the Streamlit web interface.
"""

import streamlit as st
from utils.session_state import SessionState
from utils.ui_helpers import apply_custom_css

st.set_page_config(page_title="Context Bridge", page_icon="🌉", layout="wide")

# Apply custom styling
apply_custom_css()

SessionState.init()

# Sidebar navigation
st.sidebar.title("🌉 Context Bridge")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigate",
    ["🏠 Home", "📚 Documents", "📄 Crawled Pages", "🔍 Search"],
    index=0,
    label_visibility="collapsed",
)

# Map display names to page values
page_map = {
    "🏠 Home": "Home",
    "📚 Documents": "Documents",
    "📄 Crawled Pages": "Pages",
    "🔍 Search": "Search",
}

page_value = page_map.get(page, "Home")

if page_value == "Home":
    st.title("🌉 Context Bridge")
    st.markdown("**Unified documentation management for RAG workflows**")

    st.info(
        """
    Navigate using the sidebar:
    - 📚 **Documents**: Manage documentation sources
    - 📄 **Pages**: View and organize pages
    - 🔍 **Search**: Search documentation content
    """
    )

    # Quick stats
    if st.session_state.bridge:
        # Display overall statistics
        pass

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.caption("Context Bridge v0.1.0")
    st.sidebar.caption("RAG Documentation Management")

elif page_value == "Documents":
    from pages.documents import *
elif page_value == "Pages":
    from pages.crawled_pages import *
elif page_value == "Search":
    from pages.search import *
