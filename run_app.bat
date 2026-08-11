@echo off
echo Starting Unified Medical Platform...
cd %~dp0
python -m streamlit run app.py
pause
