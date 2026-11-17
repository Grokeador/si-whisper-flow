@echo off
title SI-Whisper-Flow - Free Offline AI Voice Dictation Anywhere
echo ========================================================================
echo   SI-Whisper-Flow - 100%% Offline Voice Dictation Studio (Port 8795)
echo   Replaces Paid Wispr Flow / Superwhisper at $0.00 Cost Forever
echo ========================================================================
cd /d "%~dp0"
python "%~dp0si_whisper_flow.py" ui %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Python 3.10+ required. Verify with: python --version
    pause
)
