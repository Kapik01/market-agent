@echo off
cd /d "%~dp0"
python main.py --mode %1 >> market_agent.log 2>&1
