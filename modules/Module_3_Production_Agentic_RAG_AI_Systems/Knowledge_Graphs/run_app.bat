@echo off
REM RAG vs Knowledge Graph - Streamlit App Launcher (Windows)
REM ===========================================================

echo.
echo 🚀 Launching RAG vs Knowledge Graph Web App...
echo.
echo 📚 Learn more about building multi-agent systems:
echo 🎓 https://maven.com/boring-bot/advanced-llm?promoCode=200OFF
echo.
echo Starting Streamlit server...
echo.

REM Check if streamlit is installed
where streamlit >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Streamlit is not installed.
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Launch Streamlit
streamlit run app.py
