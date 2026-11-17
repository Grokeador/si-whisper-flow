# SI-Whisper-Flow

**Free, 100% Offline AI Voice Dictation Anywhere on Windows — Replaces \$15–25/month Cloud Apps Forever.**

Zero subscriptions. Zero weekly word limits. Your voice audio never leaves your PC.

## 3 Steps + Bonus

### Step 1 — Instant Mic, GPU & Engine Audit (`Launch_SI_Whisper_Flow.bat`)
Double-click `Launch_SI_Whisper_Flow.bat` (zero external dependencies needed to open Studio + test your Windows microphone). Automatically enumerates Windows capture microphones via `winmm.dll`, checks NVIDIA/GPU acceleration, and finds installed local Whisper backends (`faster-whisper`, `whisper.cpp`, or `openai-whisper`).

### Step 2 — Dual-Threshold Anti-Hallucination VAD & Local Whisper Engine
Prevents the classic Whisper bug of hallucinating *"Thanks for watching!"* during dead air. Strips silence automatically (`RMS + energy padding`) and supports **1-Click `faster-whisper` Installation** directly from the UI or CLI.

### Step 3 — Tech/Coding Dictionary + Spoken Commands + Clipboard-Safe Auto-Paste
Automatically fixes spoken developer terms (*"git hub"* → `GitHub`, *"ff mpeg"* → `FFmpeg`, *"pie torch"* → `PyTorch`, *"comfy u i"* → `ComfyUI`), handles *"new line"* / *"new paragraph"* / *"period"*, optionally polishes grammar via local Ollama (`:11434`), and pastes straight into VS Code, Cursor, Chrome, or Discord while restoring your original Windows clipboard.

### Bonus — Global `Ctrl+Space` Push-to-Talk & `.srt` Caption Exporter
Run `python si_whisper_flow.py hotkey` for always-on push-to-talk dictation, or export instant `.srt` subtitles from transcripts for YouTube & meetings.

## Verify Locally
```powershell
python -m unittest test_whisper_flow.py -v
```
