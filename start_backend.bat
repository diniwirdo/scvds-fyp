@echo off
echo Activating Conda environment...
call C:\Users\diniw\miniconda3\Scripts\activate.bat solgnn
cd /d "C:\FYP\gnn-smart-contract-vuln-detector - Copy\FYP2\backend"
echo Starting backend server...
python main.py
pause