@echo off
cd /d "%~dp0"
call conda activate content-understanding
streamlit run app.py
pause
