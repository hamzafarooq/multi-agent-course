#!/bin/bash

# RAG vs Knowledge Graph - Streamlit App Launcher
# =================================================

echo "🚀 Launching RAG vs Knowledge Graph Web App..."
echo ""
echo "📚 Learn more about building multi-agent systems:"
echo "🎓 https://maven.com/boring-bot/advanced-llm?promoCode=200OFF"
echo ""
echo "Starting Streamlit server..."
echo ""

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null
then
    echo "❌ Streamlit is not installed."
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Launch Streamlit
streamlit run app.py
