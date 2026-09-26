"""RAG vs ReAct demo.  Run from this folder:  .venv/bin/streamlit run main.py"""

import streamlit as st

st.set_page_config(page_title="RAG vs ReAct", page_icon="🧭", layout="wide")
st.navigation([
    st.Page("views/overview.py", title="Overview", icon="🏠", default=True),
    st.Page("app.py", title="Compare", icon="🧭"),
    st.Page("views/results.py", title="Results", icon="📊"),
]).run()
