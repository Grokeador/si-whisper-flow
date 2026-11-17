#!/usr/bin/env python3
"""
SI-Whisper-Flow App & CLI (Web Studio :8795 + Global Hotkey Mode + VAD/Formatter CLI).
Zero external pip dependencies needed to inspect mics, run VAD silence trimming, format coding text,
export .srt subtitles, or install faster-whisper in 1 click.
"""

from __future__ import annotations

import argparse
import ctypes
import html
import json
import subprocess
import sys
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from whisper_flow_engine import (
    analyze_and_trim_wav_vad,
    create_sample_speech_wav,
    default_state_dir,
    detect_whisper_environment,
    export_srt_subtitles,
    format_dictation_text,
    load_dictionary,
    paste_text_into_active_window_windows,
    record_mic_wav,
    save_dictionary_term,
    transcribe_audio_file,
)


APP_VERSION = "1.0.0"


def _render_ui(
    view: str = "audit",
    custom_home: Path | None = None,
    banner: str = "",
    vad_demo: dict[str, Any] | None = None,
    formatted_preview: str = "",
) -> str:
    env = detect_whisper_environment()
    sdir = default_state_dir(custom_home)
    dict_terms = load_dictionary(custom_home)
    mics = env["microphones"].get("devices") or []
    mic_txt = "\n".join(f"[{m['id']}] {m['name']} ({m['channels']} ch)" for m in mics) or "No physical microphone detected (headless/VM OK — WAV test ready)"

    tabs = [
        ("audit", "Step 1: Mic, GPU & Engine Audit"),
        ("vad", "Step 2: Anti-Hallucination VAD & Install"),
        ("dict", "Step 3: Coding Dictionary & Auto-Paste"),
        ("bonus", "Bonus: Global Hotkey & .SRT Export"),
    ]
    tabs_html = "".join(f'<a href="/?view={k}" class="tab {"active" if view == k else ""}">{html.escape(v)}</a>' for k, v in tabs)
    banner_html = f'<div class="banner">{html.escape(banner)}</div>' if banner else ""

    if view == "vad":
        v_txt = json.dumps(vad_demo, indent=2) if vad_demo else "Click 'Test VAD Silence Trimmer' below to generate a speech+silence WAV and verify hallucination protection!"
        content = f"""
        <div class="grid-2">
          <div class="panel">
            <h2>Step 2: Stop Whisper From Hallucinating on Silence</h2>
            <p class="sub">Whisper invents fake sentences when fed silent frames. Our Dual-Threshold RMS Energy Trimmer strips dead air before inference.</p>
            <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:12px;">
              <form method="POST" action="/api/vad-demo"><button class="btn primary" type="submit">Test VAD Silence Trimmer Now</button></form>
              <form method="POST" action="/api/install-whisper"><button class="btn" type="submit">1-Click Install faster-whisper (Free)</button></form>
            </div>
            <pre class="code">{html.escape(v_txt)}</pre>
          </div>
          <div class="panel">
            <h2>Mic Capture Test (Windows winmm.dll)</h2>
            <p class="sub">Records 3 seconds straight from your default Windows mic into 16kHz mono PCM WAV — zero PyAudio compile errors.</p>
            <form method="POST" action="/api/record-test" style="margin-bottom:12px;">
              <button class="btn warn" type="submit">Record 3s Mic Sample &amp; Run VAD</button>
            </form>
            <pre class="code">Engine Detected : {html.escape(env['active_backend'])}
GPU / CUDA      : {html.escape(env['gpu'])} (CUDA Ready: {env['cuda_ready']})
Ollama Clean    : {env['ollama_installed']}</pre>
          </div>
        </div>
        """
    elif view == "dict":
        preview_out = formatted_preview or format_dictation_text(
            "um check git hub actions then run ff mpeg with pie torch comma new line open paren local ollama close paren period",
            custom_dict=dict_terms,
        )
        dict_lines = "\n".join(f'"{k}" -> "{v}"' for k, v in list(dict_terms.items())[:14])
        content = f"""
        <div class="grid-2">
          <div class="panel">
            <h2>Step 3: Tech &amp; Coding Formatter + Auto-Paste</h2>
            <form method="POST" action="/api/format-test" style="display:flex;flex-direction:column;gap:8px;margin-bottom:12px;">
              <input class="inp" type="text" name="raw_text" value="um push to git hub then test ff mpeg and pie torch new line open paren local cuda close paren period" />
              <button class="btn primary" type="submit">Clean Spoken Transcript &amp; Test Dictionary</button>
            </form>
            <pre class="code">{html.escape(preview_out)}</pre>
          </div>
          <div class="panel">
            <h2>Custom Developer Dictionary ({len(dict_terms)} Rules Active)</h2>
            <form method="POST" action="/api/add-term" style="display:flex;gap:8px;margin-bottom:12px;">
              <input class="inp" type="text" name="spoken" placeholder="spoken (e.g. cube control)" />
              <input class="inp" type="text" name="replacement" placeholder="exact (e.g. kubectl)" />
              <button class="btn" type="submit">Save Term</button>
            </form>
            <pre class="code">{html.escape(dict_lines)}</pre>
          </div>
        </div>
        """
    elif view == "bonus":
        content = f"""
        <div class="grid-2">
          <div class="panel">
            <h2>Bonus: Always-On Global Hotkey (Ctrl+Shift+Space)</h2>
            <p class="sub">Run Push-to-Talk in background across VS Code, Cursor, Chrome, Word, or Discord with Clipboard Save &amp; Restore.</p>
            <pre class="code">PS: cd C:/YOUTUBE/TOOLS/si-whisper-flow
PS: python si_whisper_flow.py hotkey

How Auto-Paste Keeps Your Clipboard Safe:
1. Saves whatever text you had copied earlier
2. Pastes cleaned dictation directly where your cursor sits
3. Restores your previous clipboard item automatically</pre>
          </div>
          <div class="panel">
            <h2>Instant .SRT Captions Export</h2>
            <p class="sub">Turn any recorded voice note or tutorial draft straight into clean .SRT subtitles in 1 click.</p>
            <form method="POST" action="/api/export-srt" style="margin-bottom:12px;">
              <button class="btn primary" type="submit">Export Sample Clean .SRT File</button>
            </form>
            <pre class="code">Output Folder: {html.escape(str(sdir))}</pre>
          </div>
        </div>
        """
    else:
        content = f"""
        <div class="grid-2">
          <div class="panel">
            <h2>Step 1: Hardware, Mic &amp; Offline AI Audit ($0.00)</h2>
            <div class="metrics">
              <div class="m"><span>Microphones</span><strong style="color:#38bdf8">{env['microphones'].get('device_count', 0)} detected</strong></div>
              <div class="m"><span>GPU Accelerator</span><strong style="color:#34d399">{html.escape(env['gpu'][:26])}</strong></div>
              <div class="m"><span>Whisper Engine</span><strong>{html.escape(env['active_backend'][:24])}</strong></div>
              <div class="m"><span>Monthly Cloud Cost</span><strong style="color:#34d399">$0.00 Forever</strong></div>
            </div>
            <pre class="code">[Capture Devices]
{html.escape(mic_txt)}</pre>
          </div>
          <div class="panel">
            <h2>Replaces Paid Voice Apps ($15–$25/mo) Offline</h2>
            <pre class="code">- Audio stays 100% private on your Windows hardware
- Dual-threshold VAD blocks silence hallucinations
- Clipboard-Safe Ctrl+V paste into VS Code, Cursor, Word &amp; Chrome
- Tech dictionary auto-fixes GitHub, PyTorch, FFmpeg, MCP, Ollama</pre>
          </div>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8" /><title>SI-Whisper-Flow {APP_VERSION}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, sans-serif; }}
  body {{ background: #060a13; color: #f8fafc; padding: 20px 28px; }}
  .topbar {{ display: flex; justify-content: space-between; align-items: center; padding: 14px 20px; background: #0d1526; border: 2px solid #1e293b; border-radius: 12px; margin-bottom: 14px; }}
  .brand {{ font-size: 22px; font-weight: 800; }}
  .brand span {{ color: #38bdf8; }}
  .badge {{ font-size: 13px; padding: 5px 12px; border-radius: 999px; border: 1px solid #34d399; color: #34d399; font-weight: 700; }}
  .tabs {{ display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }}
  .tab {{ text-decoration: none; padding: 9px 15px; border-radius: 8px; background: #0d1526; border: 2px solid #1e293b; color: #94a3b8; font-weight: 700; font-size: 14px; }}
  .tab.active {{ background: #111c33; border-color: #38bdf8; color: #f8fafc; }}
  .banner {{ padding: 11px 16px; margin-bottom: 14px; border-radius: 8px; border: 2px solid #34d399; background: #0f2922; color: #ecfdf5; font-weight: 600; font-size: 14px; }}
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }}
  .panel {{ background: #0d1526; border: 2px solid #1e293b; border-radius: 12px; padding: 18px; }}
  h2 {{ font-size: 18px; margin-bottom: 10px; color: #38bdf8; }}
  .sub {{ color: #94a3b8; font-size: 13px; margin-bottom: 12px; }}
  .metrics {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 12px; }}
  .m {{ background: #04070e; border: 1px solid #1e293b; border-radius: 8px; padding: 10px; }}
  .m span {{ display: block; font-size: 11px; color: #94a3b8; text-transform: uppercase; }}
  .m strong {{ font-size: 14px; }}
  pre.code {{ background: #04070e; border: 1px solid #1e293b; border-radius: 8px; padding: 12px; font-family: 'Cascadia Code', Consolas, monospace; font-size: 13px; line-height: 1.45; white-space: pre-wrap; color: #e2e8f0; }}
  .btn {{ cursor: pointer; padding: 10px 14px; border-radius: 8px; border: 1px solid #334155; background: #1e293b; color: #f8fafc; font-weight: 700; font-size: 13px; }}
  .btn.primary {{ border-color: #38bdf8; background: #38bdf8; color: #020617; }}
  .btn.warn {{ border-color: #f59e0b; background: #f59e0b; color: #1c1917; }}
  .inp {{ flex: 1; padding: 8px 12px; border-radius: 8px; border: 1px solid #334155; background: #04070e; color: #f8fafc; font-size: 13px; }}
</style></head>
<body>
  <div class="topbar">
    <div class="brand">SI-Whisper-<span>Flow {APP_VERSION}</span> &bull; 100% Offline AI Voice Dictation</div>
    <span class="badge">$0.00 Forever &bull; Anti-Hallucination VAD</span>
  </div>
  <div class="tabs">{tabs_html}</div>
  {banner_html}
  {content}
</body></html>"""


def start_ui_server(port: int = 8795, custom_home: Path | None = None) -> ThreadingHTTPServer:
    sdir = default_state_dir(custom_home)
    state: dict[str, Any] = {"banner": "", "vad_demo": None, "formatted_preview": ""}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            return

        def _redirect(self, loc: str, msg: str) -> None:
            state["banner"] = msg
            self.send_response(303)
            self.send_header("Location", loc)
            self.end_headers()

        def do_GET(self) -> None:  # noqa: N802
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query)
            view = (qs.get("view") or ["audit"])[0]
            msg = state["banner"]
            state["banner"] = ""
            body = _render_ui(
                view=view,
                custom_home=custom_home,
                banner=msg,
                vad_demo=state["vad_demo"],
                formatted_preview=state["formatted_preview"],
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:  # noqa: N802
            cl = int(self.headers.get("Content-Length", "0") or "0")
            raw = self.rfile.read(cl).decode("utf-8", errors="ignore")
            form = urllib.parse.parse_qs(raw)

            if self.path == "/api/vad-demo":
                wav = create_sample_speech_wav(sdir / "sample_voice_demo.wav")
                res = analyze_and_trim_wav_vad(wav, trimmed_out=sdir / "sample_voice_trimmed.wav")
                state["vad_demo"] = res
                self._redirect("/?view=vad", f"VAD Trimmed 2.4s -> {res['trimmed_sec']}s cleanly (speech_ratio={res['speech_ratio']})!")
            elif self.path == "/api/record-test":
                rec = record_mic_wav(sdir / "mic_live_test.wav", duration_sec=2.5)
                if rec.get("ok"):
                    vad = analyze_and_trim_wav_vad(rec["wav_path"], trimmed_out=sdir / "mic_live_trimmed.wav")
                    state["vad_demo"] = {"recording": rec, "vad": vad}
                    self._redirect("/?view=vad", f"Recorded {rec['duration_sec']}s mic audio -> has_speech={vad['has_speech']}")
                else:
                    self._redirect("/?view=vad", f"Mic notice: {rec.get('error')}")
            elif self.path == "/api/install-whisper":
                proc = subprocess.run([sys.executable, "-m", "pip", "install", "faster-whisper"], capture_output=True, text=True, timeout=180)
                if proc.returncode == 0:
                    self._redirect("/?view=vad", "faster-whisper installed cleanly! Offline transcription ready.")
                else:
                    self._redirect("/?view=vad", f"Install output: {(proc.stderr or proc.stdout).strip()[:180]}")
            elif self.path == "/api/format-test":
                raw_txt = (form.get("raw_text") or [""])[0]
                cleaned = format_dictation_text(raw_txt, custom_dict=load_dictionary(custom_home))
                state["formatted_preview"] = cleaned
                self._redirect("/?view=dict", "Formatted & fixed developer terms cleanly!")
            elif self.path == "/api/add-term":
                sp = (form.get("spoken") or [""])[0]
                rp = (form.get("replacement") or [""])[0]
                if sp and rp:
                    save_dictionary_term(sp, rp, custom_home=custom_home)
                    self._redirect("/?view=dict", f"Saved custom term '{sp}' -> '{rp}'!")
                else:
                    self._redirect("/?view=dict", "Provide both spoken and exact replacement text.")
            elif self.path == "/api/export-srt":
                out = export_srt_subtitles(
                    [(0.0, 2.4, "GitHub CI passed across Python 3.12."), (2.5, 5.1, "Zero-cost local dictation ready.")],
                    sdir / "dictated_captions.srt",
                )
                self._redirect("/?view=bonus", f"Exported clean .SRT subtitles -> {out}")
            else:
                self._redirect("/?view=audit", "OK")

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def run_hotkey_listener(model_size: str = "base.en") -> None:
    """Register global Ctrl+Shift+Space hotkey on Windows for Push-to-Talk dictation."""
    if os.name != "nt":
        print("Global RegisterHotKey is supported on Windows.")
        return

    user32 = ctypes.windll.user32
    MOD_CONTROL = 0x0002
    MOD_SHIFT = 0x0004
    VK_SPACE = 0x20
    WM_HOTKEY = 0x0312
    HOTKEY_ID = 101

    if not user32.RegisterHotKey(None, HOTKEY_ID, MOD_CONTROL | MOD_SHIFT, VK_SPACE):
        raise RuntimeError("Could not register Ctrl+Shift+Space hotkey (already in use).")

    print("SI-Whisper-Flow Global Hotkey ACTIVE: Press Ctrl+Shift+Space to record 4s & auto-paste! (Ctrl+C to exit)")
    msg = ctypes.wintypes.MSG() if hasattr(ctypes, "wintypes") else None
    import ctypes.wintypes
    msg = ctypes.wintypes.MSG()
    sdir = default_state_dir()
    try:
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                wav = sdir / "hotkey_capture.wav"
                rec = record_mic_wav(wav, duration_sec=4.0)
                if rec.get("ok"):
                    tx = transcribe_audio_file(wav, model_size=model_size)
                    if tx.get("ok") and tx.get("formatted_text"):
                        paste_text_into_active_window_windows(tx["formatted_text"])
                        print("[PASTED]", tx["formatted_text"])
                    else:
                        print("[INFO]", tx.get("reason") or tx.get("error"))
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    finally:
        user32.UnregisterHotKey(None, HOTKEY_ID)


def main() -> None:
    parser = argparse.ArgumentParser(description="SI-Whisper-Flow Offline AI Voice Dictation")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("audit", help="Inspect microphones, GPU, and installed Whisper engines")
    p_vad = sub.add_parser("vad-test", help="Run dual-threshold VAD silence trim on a WAV")
    p_vad.add_argument("wav", type=Path)
    p_vad.add_argument("--out", type=Path, default=None)

    p_hk = sub.add_parser("hotkey", help="Run always-on Ctrl+Shift+Space push-to-talk hotkey")
    p_hk.add_argument("--model", default="base.en")

    p_ui = sub.add_parser("ui", help="Start Web Studio UI on port 8795")
    p_ui.add_argument("--port", type=int, default=8795)

    args = parser.parse_args()
    cmd = args.cmd or "ui"
    if cmd == "audit":
        print(json.dumps(detect_whisper_environment(), indent=2))
    elif cmd == "vad-test":
        print(json.dumps(analyze_and_trim_wav_vad(args.wav, trimmed_out=args.out), indent=2))
    elif cmd == "hotkey":
        run_hotkey_listener(model_size=args.model)
    else:
        srv = start_ui_server(port=args.port)
        url = f"http://127.0.0.1:{srv.server_address[1]}/"
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        edge = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
        if edge.exists():
            subprocess.Popen([str(edge), f"--app={url}", "--window-size=1480,920"])
        else:
            webbrowser.open(url)
        print(f"SI-Whisper-Flow Studio active at {url}")
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            srv.shutdown()


if __name__ == "__main__":
    main()
