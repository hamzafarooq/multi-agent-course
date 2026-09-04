"""
Modern Streamlit App for RAG vs Knowledge Graph Evaluation
===========================================================

A beautiful, minimal interface for comparing RAG and Knowledge Graph approaches.

Learn more: https://maven.com/boring-bot/advanced-llm?promoCode=200OFF
"""

import streamlit as st
import time
from knowledge_graph_rag_comparison import Neo4jGraphRAG
from streamlit_helper import get_comparison_results
import json
from typing import Dict, Any
import plotly.graph_objects as go
import os
from dotenv import load_dotenv
import streamlit.components.v1 as components
from pyvis.network import Network
import tempfile

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="RAG vs Knowledge Graph",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for minimal, light theme design with Mona Sans
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Mona Sans font */
    @font-face {
        font-family: 'Mona Sans';
        src: url('https://github.com/github/mona-sans/raw/main/fonts/variable/Mona-Sans.woff2') format('woff2');
        font-weight: 200 900;
        font-stretch: 75% 125%;
    }

    /* Light theme colors - minimal palette */
    :root {
        --primary: #0969da;
        --text-primary: #24292f;
        --text-secondary: #57606a;
        --text-tertiary: #6e7781;
        --bg-primary: #ffffff;
        --bg-secondary: #f6f8fa;
        --border: #d0d7de;
        --border-light: #e8eaed;
        --success: #1a7f37;
        --accent: #0969da;
    }

    /* Global font */
    * {
        font-family: 'Mona Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Hide sidebar */
    [data-testid="stSidebar"] {display: none;}
    section[data-testid="stSidebar"] {display: none;}
    .css-1d391kg {display: none;} /* sidebar toggle */

    /* Main container */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 1200px;
    }

    /* Remove extra spacing from first element */
    .main .block-container > div:first-child {
        padding-top: 0 !important;
    }

    /* Remove default container styling */
    [data-testid="stVerticalBlock"] > div:first-child {
        padding-top: 0;
    }

    /* Remove empty blocks */
    div[data-testid="stVerticalBlock"]:empty {
        display: none;
    }

    /* Minimal header card */
    .custom-card {
        background: var(--bg-primary);
        padding: 1.25rem 1.5rem;
        border-radius: 8px;
        border: 1px solid var(--border-light);
        margin-bottom: 1rem;
    }

    /* Result cards - clean and minimal */
    .result-card {
        background: var(--bg-primary);
        border: 1px solid var(--border-light);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.75rem;
    }

    .winner-card {
        background: var(--bg-primary);
        border: 2px solid var(--success);
    }

    /* Typography - clean and readable */
    .big-title {
        font-size: 2rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }

    .subtitle {
        font-size: 1rem;
        color: var(--text-secondary);
        font-weight: 400;
    }

    .section-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 1rem;
        letter-spacing: -0.01em;
    }

    /* Minimal buttons */
    .stButton > button {
        background: var(--text-primary);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        font-size: 0.875rem;
        transition: opacity 0.2s;
        width: 100%;
    }

    .stButton > button:hover {
        opacity: 0.85;
    }

    .stButton > button[kind="primary"] {
        background: var(--primary);
    }

    /* Clean input fields */
    .stTextInput > div > div > input {
        border-radius: 6px;
        border: 1px solid var(--border);
        padding: 0.5rem 0.75rem;
        font-size: 0.875rem;
        background: var(--bg-primary);
        color: var(--text-primary);
    }

    .stTextInput > div > div > input:focus {
        border-color: var(--primary);
        outline: none;
        box-shadow: 0 0 0 3px rgba(9, 105, 218, 0.1);
    }

    /* Minimal score badges */
    .score-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-weight: 500;
        font-size: 0.75rem;
        margin: 0.25rem;
        border: 1px solid var(--border-light);
    }

    .score-high {
        background: #dafbe1;
        color: var(--success);
        border-color: #9cd6a8;
    }

    .score-medium {
        background: #fff8c5;
        color: #7d4e00;
        border-color: #e8d87f;
    }

    .score-low {
        background: #ffebe9;
        color: #cf222e;
        border-color: #ffcecb;
    }

    /* Clean code blocks */
    .stCodeBlock {
        border-radius: 6px;
        border: 1px solid var(--border-light);
    }

    /* Minimal expander */
    .streamlit-expanderHeader {
        font-weight: 500;
        color: var(--text-primary);
        font-size: 0.875rem;
    }

    /* Info/warning/error boxes */
    .stAlert {
        border-radius: 6px;
        border: 1px solid var(--border-light);
    }

    /* Metrics - cleaner style */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--text-primary);
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.75rem;
        color: var(--text-secondary);
        font-weight: 500;
    }

    /* Sidebar minimal styling */
    [data-testid="stSidebar"] {
        background: var(--bg-secondary);
    }

    /* Success/error messages */
    .stSuccess, .stError, .stWarning, .stInfo {
        border-radius: 6px;
        font-size: 0.875rem;
    }

    /* Checkbox */
    .stCheckbox {
        font-size: 0.875rem;
    }

    /* Selectbox */
    .stSelectbox {
        font-size: 0.875rem;
    }

    /* Course CTA hover effect */
    a[href*="maven.com"]:hover {
        opacity: 0.9;
    }

    /* Course image styling */
    img[alt*="Agent Engineering"] {
        border-bottom: 1px solid var(--border-light);
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if 'rag_system' not in st.session_state:
        st.session_state.rag_system = None
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'comparison_result' not in st.session_state:
        st.session_state.comparison_result = None
    if 'show_full_graph' not in st.session_state:
        st.session_state.show_full_graph = False
    if 'graph_node_limit' not in st.session_state:
        st.session_state.graph_node_limit = 50


def load_rag_system():
    """Initialize and check the RAG system."""
    try:
        with st.spinner("🔌 Connecting to Neo4j..."):
            rag = Neo4jGraphRAG()

        # Check if data exists
        with st.spinner("📊 Checking database..."):
            count = rag.execute_query("MATCH (n) RETURN count(n) as count")

            if count[0]['count'] == 0:
                st.error("❌ No data found in Neo4j database!")
                st.warning("⚠️ Please run the setup script first:")
                st.code("python setup.py", language="bash")
                st.info("💡 The setup script will load the dataset and create embeddings. This only needs to be done once.")
                rag.close()
                return False

            # Check if embeddings exist
            emb_count = rag.execute_query(
                "MATCH (a:Article) WHERE a.embedding IS NOT NULL RETURN count(a) as count"
            )

            if emb_count[0]['count'] == 0:
                st.warning("⚠️ Embeddings not found. Please run setup:")
                st.code("python setup.py", language="bash")
                rag.close()
                return False

            st.success(f"✅ System ready! {count[0]['count']} nodes loaded, {emb_count[0]['count']} embeddings available.")

        st.session_state.rag_system = rag
        st.session_state.data_loaded = True
        return True

    except Exception as e:
        st.error(f"❌ Error connecting to Neo4j: {str(e)}")
        st.warning("💡 Troubleshooting tips:")
        st.markdown("""
        1. Check your `.env` file has correct credentials
        2. Verify your Neo4j instance is running
        3. Make sure you've run `python setup.py` first
        """)
        return False


def display_hero_section(show_button=False, button_label="", button_key=""):
    """Display the hero section with title and description."""
    # Use container to apply card styling
    with st.container():
        col1, col2 = st.columns([2.5, 1])

        with col1:
            st.markdown("""
            <div style="padding-top: 0.25rem;">
                <h1 style="font-size: 1.5rem; margin: 0; font-weight: 600; color: #cf222e; letter-spacing: -0.02em;">
                    RAG vs Knowledge Graph Comparison
                </h1>
                <p style="font-size: 0.8125rem; color: var(--text-secondary); margin-top: 0.5rem; margin-bottom: 0.25rem; font-weight: 400; line-height: 1.5;">
                    Compare Retrieval-Augmented Generation (RAG) and Knowledge Graph approaches for question-answering.
                    See which method performs better for different types of questions with LLM-based evaluation.
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            if show_button and button_label:
                st.markdown('<div style="padding-top: 0.25rem;"></div>', unsafe_allow_html=True)
                return st.button(button_label, use_container_width=True, key=button_key)

    # Divider
    st.markdown('<div style="height: 1rem;"></div>', unsafe_allow_html=True)
    return False


def display_method_card(title: str, emoji: str, description: str, features: list):
    """Display a method information card."""
    st.markdown(f"""
    <div class="result-card">
        <h3 style="margin: 0; color: var(--text-primary); font-size: 0.9375rem; font-weight: 600; letter-spacing: -0.01em;">
            {emoji} {title}
        </h3>
        <p style="color: var(--text-secondary); margin: 0.5rem 0 0.75rem 0; font-size: 0.8125rem; line-height: 1.4;">
            {description}
        </p>
        <div style="margin-top: 0.5rem;">
            {''.join([f'<div style="margin: 0.25rem 0; font-size: 0.75rem; color: var(--text-secondary);"><span style="color: var(--success); font-weight: 500;">✓</span> {feature}</div>' for feature in features])}
        </div>
    </div>
    """, unsafe_allow_html=True)


def display_result_card(title: str, emoji: str, answer: str, metadata: Dict, is_winner: bool = False):
    """Display a result card with answer and metadata."""
    card_class = "result-card winner-card" if is_winner else "result-card"

    st.markdown(f"""
    <div class="{card_class}">
        <h3 style="margin: 0 0 0.5rem 0; font-size: 1rem; font-weight: 600; color: var(--text-primary); letter-spacing: -0.01em;">
            {emoji} {title}
        </h3>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"<div style='font-size: 0.8125rem; line-height: 1.5; color: var(--text-primary); margin: 0.5rem 0;'>{answer}</div>", unsafe_allow_html=True)

    # Display metadata
    cols = st.columns(len(metadata))
    for col, (key, value) in zip(cols, metadata.items()):
        with col:
            st.metric(key, value)


def get_score_badge_html(score: float, max_score: float = 10) -> str:
    """Generate HTML for a score badge."""
    percentage = (score / max_score) * 100

    if percentage >= 80:
        badge_class = "score-high"
    elif percentage >= 60:
        badge_class = "score-medium"
    else:
        badge_class = "score-low"

    return f'<span class="score-badge {badge_class}">{score}/{max_score}</span>'


def display_judge_verdict_progressive(judgment: Dict, scores_container, reasoning_container,
                                    strengths_container, recommendation_container):
    """Display the LLM judge's verdict progressively with colored strengths/weaknesses."""
    st.markdown('<div style="height: 0.75rem;"></div>', unsafe_allow_html=True)
    st.markdown('<h2 style="font-size: 0.9375rem; font-weight: 600; color: var(--text-primary); margin-bottom: 0.5rem; letter-spacing: -0.01em;">⚖️ LLM Judge Verdict</h2>', unsafe_allow_html=True)

    # Winner announcement
    winner_map = {"A": "RAG", "B": "Knowledge Graph", "TIE": "TIE"}
    winner = winner_map.get(judgment.get('winner', 'UNKNOWN'), 'UNKNOWN')
    confidence = judgment.get('confidence', 'unknown').capitalize()

    st.markdown(f"""
    <div class="result-card winner-card">
        <h2 style="margin: 0; font-size: 1.25rem; font-weight: 600; text-align: center; color: var(--text-primary);">
            Winner: {winner}
        </h2>
        <p style="text-align: center; font-size: 0.75rem; margin-top: 0.25rem; color: var(--text-secondary); font-weight: 500;">
            Confidence: {confidence}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Scores comparison
    with scores_container.container():
        st.markdown('<h3 style="font-size: 1rem; font-weight: 600; color: var(--text-primary); margin: 1rem 0 0.5rem 0; letter-spacing: -0.01em;">Detailed Scores</h3>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            <div class="result-card">
                <h4 style="color: var(--text-primary); margin-top: 0; font-size: 0.9375rem; font-weight: 600;">📚 RAG</h4>
            """, unsafe_allow_html=True)

            accuracy = judgment.get('accuracy_score_a', 0)
            completeness = judgment.get('completeness_score_a', 0)
            precision = judgment.get('precision_score_a', 0)

            st.markdown(f"""
                <div style="margin: 0.5rem 0;">
                    <div style="margin: 0.25rem 0; font-size: 0.75rem; color: var(--text-secondary);">Accuracy: {get_score_badge_html(accuracy)}</div>
                    <div style="margin: 0.25rem 0; font-size: 0.75rem; color: var(--text-secondary);">Completeness: {get_score_badge_html(completeness)}</div>
                    <div style="margin: 0.25rem 0; font-size: 0.75rem; color: var(--text-secondary);">Precision: {get_score_badge_html(precision)}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="result-card">
                <h4 style="color: var(--text-primary); margin-top: 0; font-size: 0.9375rem; font-weight: 600;">🔍 Knowledge Graph</h4>
            """, unsafe_allow_html=True)

            accuracy = judgment.get('accuracy_score_b', 0)
            completeness = judgment.get('completeness_score_b', 0)
            precision = judgment.get('precision_score_b', 0)

            st.markdown(f"""
                <div style="margin: 0.5rem 0;">
                    <div style="margin: 0.25rem 0; font-size: 0.75rem; color: var(--text-secondary);">Accuracy: {get_score_badge_html(accuracy)}</div>
                    <div style="margin: 0.25rem 0; font-size: 0.75rem; color: var(--text-secondary);">Completeness: {get_score_badge_html(completeness)}</div>
                    <div style="margin: 0.25rem 0; font-size: 0.75rem; color: var(--text-secondary);">Precision: {get_score_badge_html(precision)}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Reasoning
    if judgment.get('reasoning'):
        with reasoning_container.container():
            st.markdown('<h3 style="font-size: 1rem; font-weight: 600; color: var(--text-primary); margin: 1rem 0 0.5rem 0; letter-spacing: -0.01em;">Reasoning</h3>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="result-card">
                <p style="line-height: 1.5; color: var(--text-secondary); font-size: 0.8125rem; margin: 0;">
                    {judgment['reasoning']}
                </p>
            </div>
            """, unsafe_allow_html=True)

    # Strengths and Weaknesses with colors
    with strengths_container.container():
        col1, col2 = st.columns(2)

        with col1:
            if judgment.get('strengths_a'):
                st.markdown('<h4 style="font-size: 0.9375rem; font-weight: 600; color: var(--success); margin: 0.75rem 0 0.375rem 0;">✓ RAG Strengths</h4>', unsafe_allow_html=True)
                for strength in judgment['strengths_a']:
                    st.markdown(f"""
                    <div style='font-size: 0.75rem; color: var(--success); margin: 0.2rem 0; padding: 0.25rem 0.5rem;
                                background: #dafbe1; border-left: 3px solid var(--success); border-radius: 4px;'>
                        • {strength}
                    </div>
                    """, unsafe_allow_html=True)

            if judgment.get('weaknesses_a'):
                st.markdown('<h4 style="font-size: 0.9375rem; font-weight: 600; color: #cf222e; margin: 0.75rem 0 0.375rem 0;">− RAG Weaknesses</h4>', unsafe_allow_html=True)
                for weakness in judgment['weaknesses_a']:
                    st.markdown(f"""
                    <div style='font-size: 0.75rem; color: #cf222e; margin: 0.2rem 0; padding: 0.25rem 0.5rem;
                                background: #ffebe9; border-left: 3px solid #cf222e; border-radius: 4px;'>
                        • {weakness}
                    </div>
                    """, unsafe_allow_html=True)

        with col2:
            if judgment.get('strengths_b'):
                st.markdown('<h4 style="font-size: 0.9375rem; font-weight: 600; color: var(--success); margin: 0.75rem 0 0.375rem 0;">✓ KG Strengths</h4>', unsafe_allow_html=True)
                for strength in judgment['strengths_b']:
                    st.markdown(f"""
                    <div style='font-size: 0.75rem; color: var(--success); margin: 0.2rem 0; padding: 0.25rem 0.5rem;
                                background: #dafbe1; border-left: 3px solid var(--success); border-radius: 4px;'>
                        • {strength}
                    </div>
                    """, unsafe_allow_html=True)

            if judgment.get('weaknesses_b'):
                st.markdown('<h4 style="font-size: 0.9375rem; font-weight: 600; color: #cf222e; margin: 0.75rem 0 0.375rem 0;">− KG Weaknesses</h4>', unsafe_allow_html=True)
                for weakness in judgment['weaknesses_b']:
                    st.markdown(f"""
                    <div style='font-size: 0.75rem; color: #cf222e; margin: 0.2rem 0; padding: 0.25rem 0.5rem;
                                background: #ffebe9; border-left: 3px solid #cf222e; border-radius: 4px;'>
                        • {weakness}
                    </div>
                    """, unsafe_allow_html=True)

    # Recommendation
    if judgment.get('recommendation'):
        with recommendation_container.container():
            st.markdown('<h3 style="font-size: 1rem; font-weight: 600; color: var(--text-primary); margin: 1rem 0 0.5rem 0; letter-spacing: -0.01em;">Recommendation</h3>', unsafe_allow_html=True)
            st.markdown(f"<div class='result-card' style='font-size: 0.8125rem; color: var(--text-secondary); line-height: 1.5;'>{judgment['recommendation']}</div>", unsafe_allow_html=True)


def display_judge_verdict(judgment: Dict):
    """Display the LLM judge's verdict in a minimal format."""
    st.markdown('<div style="height: 0.75rem;"></div>', unsafe_allow_html=True)
    st.markdown('<h2 style="font-size: 0.9375rem; font-weight: 600; color: var(--text-primary); margin-bottom: 0.5rem; letter-spacing: -0.01em;">⚖️ LLM Judge Verdict</h2>', unsafe_allow_html=True)

    # Winner announcement
    winner_map = {"A": "RAG", "B": "Knowledge Graph", "TIE": "TIE"}
    winner = winner_map.get(judgment.get('winner', 'UNKNOWN'), 'UNKNOWN')
    confidence = judgment.get('confidence', 'unknown').capitalize()

    st.markdown(f"""
    <div class="result-card winner-card">
        <h2 style="margin: 0; font-size: 1.25rem; font-weight: 600; text-align: center; color: var(--text-primary);">
            Winner: {winner}
        </h2>
        <p style="text-align: center; font-size: 0.75rem; margin-top: 0.25rem; color: var(--text-secondary); font-weight: 500;">
            Confidence: {confidence}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Scores comparison
    st.markdown('<h3 style="font-size: 1rem; font-weight: 600; color: var(--text-primary); margin: 1rem 0 0.5rem 0; letter-spacing: -0.01em;">Detailed Scores</h3>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="result-card">
            <h4 style="color: var(--text-primary); margin-top: 0; font-size: 0.9375rem; font-weight: 600;">📚 RAG</h4>
        """, unsafe_allow_html=True)

        accuracy = judgment.get('accuracy_score_a', 0)
        completeness = judgment.get('completeness_score_a', 0)
        precision = judgment.get('precision_score_a', 0)

        st.markdown(f"""
            <div style="margin: 0.5rem 0;">
                <div style="margin: 0.25rem 0; font-size: 0.75rem; color: var(--text-secondary);">Accuracy: {get_score_badge_html(accuracy)}</div>
                <div style="margin: 0.25rem 0; font-size: 0.75rem; color: var(--text-secondary);">Completeness: {get_score_badge_html(completeness)}</div>
                <div style="margin: 0.25rem 0; font-size: 0.75rem; color: var(--text-secondary);">Precision: {get_score_badge_html(precision)}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="result-card">
            <h4 style="color: var(--text-primary); margin-top: 0; font-size: 0.9375rem; font-weight: 600;">🔍 Knowledge Graph</h4>
        """, unsafe_allow_html=True)

        accuracy = judgment.get('accuracy_score_b', 0)
        completeness = judgment.get('completeness_score_b', 0)
        precision = judgment.get('precision_score_b', 0)

        st.markdown(f"""
            <div style="margin: 0.5rem 0;">
                <div style="margin: 0.25rem 0; font-size: 0.75rem; color: var(--text-secondary);">Accuracy: {get_score_badge_html(accuracy)}</div>
                <div style="margin: 0.25rem 0; font-size: 0.75rem; color: var(--text-secondary);">Completeness: {get_score_badge_html(completeness)}</div>
                <div style="margin: 0.25rem 0; font-size: 0.75rem; color: var(--text-secondary);">Precision: {get_score_badge_html(precision)}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Reasoning
    if judgment.get('reasoning'):
        st.markdown('<h3 style="font-size: 1rem; font-weight: 600; color: var(--text-primary); margin: 1rem 0 0.5rem 0; letter-spacing: -0.01em;">Reasoning</h3>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="result-card">
            <p style="line-height: 1.5; color: var(--text-secondary); font-size: 0.8125rem; margin: 0;">
                {judgment['reasoning']}
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Strengths and Weaknesses
    col1, col2 = st.columns(2)

    with col1:
        if judgment.get('strengths_a'):
            st.markdown('<h4 style="font-size: 0.9375rem; font-weight: 600; color: var(--text-primary); margin: 0.75rem 0 0.375rem 0;">✓ RAG Strengths</h4>', unsafe_allow_html=True)
            for strength in judgment['strengths_a']:
                st.markdown(f"<div style='font-size: 0.75rem; color: var(--text-secondary); margin: 0.2rem 0; padding-left: 1rem;'>• {strength}</div>", unsafe_allow_html=True)

        if judgment.get('weaknesses_a'):
            st.markdown('<h4 style="font-size: 0.9375rem; font-weight: 600; color: var(--text-primary); margin: 0.75rem 0 0.375rem 0;">− RAG Weaknesses</h4>', unsafe_allow_html=True)
            for weakness in judgment['weaknesses_a']:
                st.markdown(f"<div style='font-size: 0.75rem; color: var(--text-secondary); margin: 0.2rem 0; padding-left: 1rem;'>• {weakness}</div>", unsafe_allow_html=True)

    with col2:
        if judgment.get('strengths_b'):
            st.markdown('<h4 style="font-size: 0.9375rem; font-weight: 600; color: var(--text-primary); margin: 0.75rem 0 0.375rem 0;">✓ KG Strengths</h4>', unsafe_allow_html=True)
            for strength in judgment['strengths_b']:
                st.markdown(f"<div style='font-size: 0.75rem; color: var(--text-secondary); margin: 0.2rem 0; padding-left: 1rem;'>• {strength}</div>", unsafe_allow_html=True)

        if judgment.get('weaknesses_b'):
            st.markdown('<h4 style="font-size: 0.9375rem; font-weight: 600; color: var(--text-primary); margin: 0.75rem 0 0.375rem 0;">− KG Weaknesses</h4>', unsafe_allow_html=True)
            for weakness in judgment['weaknesses_b']:
                st.markdown(f"<div style='font-size: 0.75rem; color: var(--text-secondary); margin: 0.2rem 0; padding-left: 1rem;'>• {weakness}</div>", unsafe_allow_html=True)

    # Recommendation
    if judgment.get('recommendation'):
        st.markdown('<h3 style="font-size: 1rem; font-weight: 600; color: var(--text-primary); margin: 1rem 0 0.5rem 0; letter-spacing: -0.01em;">Recommendation</h3>', unsafe_allow_html=True)
        st.markdown(f"<div class='result-card' style='font-size: 0.8125rem; color: var(--text-secondary); line-height: 1.5;'>{judgment['recommendation']}</div>", unsafe_allow_html=True)


def create_comparison_chart(judgment: Dict):
    """Create a comparison chart using Plotly."""
    categories = ['Accuracy', 'Completeness', 'Precision']

    rag_scores = [
        judgment.get('accuracy_score_a', 0),
        judgment.get('completeness_score_a', 0),
        judgment.get('precision_score_a', 0)
    ]

    kg_scores = [
        judgment.get('accuracy_score_b', 0),
        judgment.get('completeness_score_b', 0),
        judgment.get('precision_score_b', 0)
    ]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=rag_scores,
        theta=categories,
        fill='toself',
        name='RAG',
        line_color='#0969da',
        fillcolor='rgba(9, 105, 218, 0.15)',
        line_width=2
    ))

    fig.add_trace(go.Scatterpolar(
        r=kg_scores,
        theta=categories,
        fill='toself',
        name='Knowledge Graph',
        line_color='#1a7f37',
        fillcolor='rgba(26, 127, 55, 0.15)',
        line_width=2
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10],
                gridcolor='#e8eaed',
                linecolor='#d0d7de'
            ),
            angularaxis=dict(
                gridcolor='#e8eaed',
                linecolor='#d0d7de'
            ),
            bgcolor='#ffffff'
        ),
        showlegend=True,
        height=300,
        margin=dict(t=20, b=20, l=20, r=20),
        paper_bgcolor='#ffffff',
        plot_bgcolor='#ffffff',
        font=dict(
            family='Mona Sans, Inter, sans-serif',
            size=11,
            color='#24292f'
        ),
        legend=dict(
            font=dict(size=10)
        )
    )

    return fig


def create_graph_visualization(rag_system: Neo4jGraphRAG, limit: int = 50):
    """
    Create an interactive graph visualization using Pyvis.

    Args:
        rag_system: Neo4jGraphRAG instance
        limit: Maximum number of nodes to display
    """
    try:
        # Get graph data
        with st.spinner("Loading graph data..."):
            graph_data = rag_system.get_graph_data(limit=limit)

        if not graph_data['nodes']:
            st.warning("No graph data available to visualize.")
            return

        _render_pyvis_graph(graph_data, height=620)

    except Exception as e:
        st.error(f"Error creating graph visualization: {str(e)}")


def create_query_graph_visualization(graph_data: Dict[str, Any]):
    """
    Create visualization for the specific subgraph used to answer a question.

    Args:
        graph_data: Dictionary with 'nodes' and 'relationships'
    """
    try:
        if not graph_data or not graph_data.get('nodes'):
            st.info("💡 No graph structure available for this query. The query may have returned simple values or aggregations rather than graph paths.")
            return

        st.markdown("""
        <div style="margin-top: 0.75rem; padding: 0.75rem; background: var(--bg-secondary); border-radius: 6px; border: 1px solid var(--border-light);">
            <div style="font-size: 0.8125rem; font-weight: 600; color: var(--text-primary); margin-bottom: 0.25rem;">
                📊 Query Graph Visualization
            </div>
            <div style="font-size: 0.75rem; color: var(--text-secondary);">
                Showing the knowledge graph path used to answer your question
            </div>
        </div>
        """, unsafe_allow_html=True)

        _render_pyvis_graph(graph_data, height=450)

    except Exception as e:
        st.error(f"Error creating query visualization: {str(e)}")


def _render_pyvis_graph(graph_data: Dict[str, Any], height: int = 600):
    """
    Internal function to render a Pyvis graph from graph data.

    Args:
        graph_data: Dictionary with 'nodes' and 'relationships'
        height: Height of the visualization in pixels
    """
    # Create Pyvis network
    net = Network(
        height=f"{height}px",
        width="100%",
        bgcolor="#ffffff",
        font_color="#24292f",
        notebook=False
    )

    # Configure physics for better layout
    net.set_options("""
    {
        "physics": {
            "enabled": true,
            "barnesHut": {
                "gravitationalConstant": -8000,
                "centralGravity": 0.3,
                "springLength": 95,
                "springConstant": 0.04,
                "damping": 0.09
            },
            "minVelocity": 0.75
        },
        "nodes": {
            "font": {
                "size": 14,
                "face": "Mona Sans, Inter, sans-serif"
            }
        },
        "edges": {
            "smooth": {
                "type": "continuous"
            },
            "font": {
                "size": 11,
                "align": "middle"
            }
        }
    }
    """)

    # Color mapping for different node types
    color_map = {
        'Researcher': '#0969da',  # Blue
        'Article': '#1a7f37',     # Green
        'Topic': '#cf222e'        # Red
    }

    # Add nodes
    for node in graph_data['nodes']:
        node_id = node['id']
        label = node['label']
        props = node['properties']

        # Create node title (hover text)
        if label == 'Researcher':
            title = f"Researcher: {props.get('name', 'Unknown')}"
            node_label = props.get('name', 'Unknown')
        elif label == 'Article':
            title = f"Article: {props.get('title', 'Unknown')[:50]}..."
            node_label = props.get('title', 'Unknown')[:30] + "..."
        elif label == 'Topic':
            title = f"Topic: {props.get('name', 'Unknown')}"
            node_label = props.get('name', 'Unknown')
        else:
            title = f"{label}: {str(props)[:50]}"
            node_label = label

        net.add_node(
            node_id,
            label=node_label,
            title=title,
            color=color_map.get(label, '#6e7781'),
            size=25 if label == 'Researcher' else 20
        )

    # Add edges
    for rel in graph_data['relationships']:
        if rel['source'] is not None and rel['target'] is not None:
            net.add_edge(
                rel['source'],
                rel['target'],
                title=rel['type'],
                label=rel['type']
            )

    # Save to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as f:
        net.save_graph(f.name)
        html_file = f.name

    # Read and display
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Clean up
    os.unlink(html_file)

    # Display in Streamlit
    components.html(html_content, height=height + 20, scrolling=False)

    # Show legend
    st.markdown("""
    <div style="margin-top: 0.5rem; padding: 0.75rem; background: var(--bg-secondary); border-radius: 6px; border: 1px solid var(--border-light);">
        <div style="font-size: 0.75rem; font-weight: 600; color: var(--text-primary); margin-bottom: 0.5rem;">Legend:</div>
        <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
            <div style="font-size: 0.75rem;"><span style="color: #0969da;">●</span> Researcher</div>
            <div style="font-size: 0.75rem;"><span style="color: #1a7f37;">●</span> Article</div>
            <div style="font-size: 0.75rem;"><span style="color: #cf222e;">●</span> Topic</div>
        </div>
        <div style="margin-top: 0.5rem; font-size: 0.6875rem; color: var(--text-tertiary);">
            💡 Drag nodes to rearrange • Scroll to zoom • Click nodes for details
        </div>
    </div>
    """, unsafe_allow_html=True)


def main():
    """Main application logic."""
    initialize_session_state()

    # Display hero section with integrated button
    if not st.session_state.data_loaded:
        button_clicked = display_hero_section(show_button=True, button_label="Initialize System", button_key="init_btn")
    else:
        button_clicked = display_hero_section(show_button=True, button_label="Reset System", button_key="reset_btn")

    # Handle button clicks after rendering
    if button_clicked:
        if not st.session_state.data_loaded:
            load_rag_system()
        else:
            st.session_state.data_loaded = False
            st.session_state.rag_system = None
            st.session_state.comparison_result = None
            st.rerun()

    # Main content
    if not st.session_state.data_loaded:
        st.markdown('<h3 style="font-size: 1rem; font-weight: 600; color: var(--text-primary); margin-bottom: 0.5rem; letter-spacing: -0.01em;">Welcome</h3>', unsafe_allow_html=True)
        st.info("Click **Initialize System** in the sidebar to get started.")

        # Show method comparison
        st.markdown('<h3 style="font-size: 0.9375rem; font-weight: 600; color: var(--text-primary); margin: 1rem 0 0.5rem 0; letter-spacing: -0.01em;">What Does This Do?</h3>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            display_method_card(
                "RAG (Retrieval-Augmented Generation)",
                "📚",
                "Uses semantic search to find relevant documents and generates answers using an LLM.",
                [
                    "Best for semantic queries",
                    "Natural language understanding",
                    "Summarization tasks",
                    "Contextual reasoning"
                ]
            )

        with col2:
            display_method_card(
                "Knowledge Graph with Text-to-Cypher",
                "🔍",
                "Converts questions to structured queries and executes them on a graph database.",
                [
                    "Best for precise counts",
                    "Relationship queries",
                    "Exact filtering",
                    "Multi-hop reasoning"
                ]
            )

        return

    # Graph Visualization Section
    st.markdown('<h3 style="font-size: 0.9375rem; font-weight: 600; color: var(--text-primary); margin: 0.75rem 0 0.5rem 0; letter-spacing: -0.01em;">Knowledge Graph Visualization</h3>', unsafe_allow_html=True)

    with st.expander("🔍 View Graph Structure", expanded=False):
        st.markdown("""
        <p style="font-size: 0.8125rem; color: var(--text-secondary); margin-bottom: 0.75rem;">
            Interactive visualization of the knowledge graph showing researchers, articles, topics, and their relationships.
        </p>
        """, unsafe_allow_html=True)

        # Controls
        node_limit = st.slider("Number of nodes to display", min_value=20, max_value=50, value=50, step=10)

        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Generate Graph", use_container_width=True):
                st.session_state.show_full_graph = True
                st.session_state.graph_node_limit = node_limit

        # Display graph if button was clicked
        if st.session_state.get('show_full_graph', False):
            create_graph_visualization(st.session_state.rag_system,
                                     limit=st.session_state.get('graph_node_limit', 50))

    st.markdown('<div style="height: 0.75rem;"></div>', unsafe_allow_html=True)

    # Question input
    st.markdown('<h3 style="font-size: 0.9375rem; font-weight: 600; color: var(--text-primary); margin: 0.75rem 0 0.5rem 0; letter-spacing: -0.01em;">Ask a Question</h3>', unsafe_allow_html=True)

    # Sample questions at the top
    sample_questions = [
        "Who are the most connected researchers in the collaboration network?",
    "Who are the collaborators of Emily Chen?",
    "How many articles has each researcher published?",
    "Show me all articles published by David Johnson",
    "Which researchers work on AI Ethics?",
    "What are the main challenges in AI safety?",
    "Which researchers work on the same topics as Emily Chen?",
    "What research was published in 2024?",
    "Compare the research focus of Emily Chen vs Michael Brown",
    "Which topic has the most publications?",
    "Explain the innovations in transformer architectures",
]
    # sample_questions = [
    #     "Who are the collaborators of Emily Chen?",
    #     "How many articles has each researcher published?",
    #     "What are the main challenges in AI safety?",
    #     "Which researchers work on AI Ethics?",
    #     "Compare the research focus of Emily Chen vs Michael Brown"
    # ]

    st.markdown('<p style="font-size: 0.8125rem; color: var(--text-secondary); margin: 0 0 0.375rem 0; font-weight: 500;">Try a sample question:</p>', unsafe_allow_html=True)
    selected_sample = st.selectbox(
        "Sample questions",
        [""] + sample_questions,
        label_visibility="collapsed"
    )

    # Question input
    question = st.text_input(
        "Enter your question:",
        value=selected_sample if selected_sample else "",
        placeholder="e.g., Who are the collaborators of Emily Chen?",
        label_visibility="collapsed",
        key="question_input"
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        compare_button = st.button(
            "Compare Both",
            use_container_width=True,
            type="primary",
            disabled=not question or question.strip() == ""
        )

    with col2:
        show_details = st.checkbox("Show Details", value=True)

    # Process comparison with progressive output
    if compare_button and question:
        try:
            st.markdown('<h3 style="font-size: 0.9375rem; font-weight: 600; color: var(--text-primary); margin: 0.75rem 0 0.5rem 0; letter-spacing: -0.01em;">Results</h3>', unsafe_allow_html=True)
            st.markdown(f"<div style='font-size: 0.8125rem; color: var(--text-secondary); margin: 0.5rem 0 0.5rem 0;'><strong>Question:</strong> {question}</div>", unsafe_allow_html=True)

            # Create placeholder containers
            col1, col2 = st.columns(2)

            with col1:
                rag_container = st.empty()
                rag_details_container = st.empty()

            with col2:
                kg_container = st.empty()
                kg_graph_container = st.empty()
                kg_details_container = st.empty()

            judge_container = st.empty()
            scores_container = st.empty()
            reasoning_container = st.empty()
            strengths_container = st.empty()
            recommendation_container = st.empty()
            chart_container = st.empty()

            # Step 1: Get RAG answer
            with rag_container.container():
                with st.spinner("Getting RAG answer..."):
                    rag_result = st.session_state.rag_system.query(question, use_vector_search=False)

                display_result_card(
                    "RAG Answer",
                    "📚",
                    rag_result['answer'],
                    {
                        "⏱️ Time": f"{rag_result['time']:.2f}s",
                        "📄 Sources": len(rag_result['sources'])
                    }
                )

            if show_details and rag_result.get('context'):
                with rag_details_container.expander("📄 View Retrieved Context"):
                    st.text(rag_result['context'][:1000] + "...")

            # Step 2: Get Knowledge Graph answer
            with kg_container.container():
                with st.spinner("Getting Knowledge Graph answer..."):
                    kg_result = st.session_state.rag_system.kg_query_with_explanation(question)

                if kg_result['success']:
                    display_result_card(
                        "Knowledge Graph Answer",
                        "🔍",
                        kg_result['answer'],
                        {
                            "⏱️ Time": f"{kg_result['time']:.2f}s",
                            "📊 Results": kg_result['result_count']
                        }
                    )
                else:
                    st.error(f"❌ Knowledge Graph query failed: {kg_result.get('error')}")
                    return

            # Show query graph visualization
            if kg_result['success'] and kg_result.get('graph_data') and kg_result['graph_data'].get('nodes'):
                with kg_graph_container.container():
                    st.markdown('<div style="height: 0.5rem;"></div>', unsafe_allow_html=True)
                    create_query_graph_visualization(kg_result['graph_data'])

            if show_details and kg_result['success']:
                with kg_details_container:
                    with st.expander("🔍 View Cypher Query"):
                        st.code(kg_result['cypher'], language="cypher")

                    if kg_result.get('results'):
                        with st.expander("📊 View Raw Results"):
                            st.json(kg_result['results'][:3])

            # Step 3: Get LLM judgment
            with st.spinner("Running LLM evaluation..."):
                from streamlit_helper import get_llm_judgment
                judgment = get_llm_judgment(question, rag_result, kg_result)

            # Display judge verdict
            if judgment and not judgment.get('error'):
                with judge_container.container():
                    display_judge_verdict_progressive(judgment, scores_container, reasoning_container,
                                                     strengths_container, recommendation_container)

                # Show comparison chart
                with chart_container.container():
                    st.markdown('<h3 style="font-size: 0.875rem; font-weight: 600; color: var(--text-primary); margin: 1rem 0 0.5rem 0; letter-spacing: -0.01em;">Visual Comparison</h3>', unsafe_allow_html=True)
                    fig = create_comparison_chart(judgment)
                    st.plotly_chart(fig, use_container_width=True)

            # Store for reference
            st.session_state.comparison_result = {
                "question": question,
                "winner": judgment.get('winner'),
                "confidence": judgment.get('confidence'),
                "judgment": judgment,
                "rag_result": rag_result,
                "kg_result": kg_result
            }

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.info("💡 If you see connection errors, make sure you ran `python setup.py` first!")
            return

    # Course CTA at the bottom
    st.markdown('<div style="height: 2rem;"></div>', unsafe_allow_html=True)

    # Course CTA container
    st.markdown('<div style="border: 1px solid var(--border-light); border-radius: 8px; overflow: hidden; margin: 2rem 0;">', unsafe_allow_html=True)

    # Display course image
    import os
    image_path = os.path.join(os.path.dirname(__file__), "course_img.png")
    if os.path.exists(image_path):
        st.image(image_path, use_column_width=True)

    # Simple CTA
    st.markdown("""
        <div style="padding: 1.5rem; background: var(--bg-primary); text-align: center;">
            <h3 style="margin: 0 0 0.75rem 0; font-size: 1.125rem; font-weight: 600; color: var(--text-primary);">
                Want to go deeper?
            </h3>
            <a href="https://maven.com/boring-bot/advanced-llm?promoCode=200OFF" target="_blank"
               style="display: inline-block; background: var(--text-primary); color: white; padding: 0.75rem 1.5rem;
                      border-radius: 6px; text-decoration: none; font-weight: 600; font-size: 0.9375rem;
                      transition: opacity 0.2s;">
                Enroll Now - Save $200 with code 200OFF →
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
