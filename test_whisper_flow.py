import math
import struct
import tempfile
import threading
import unittest
import urllib.request
import wave
from pathlib import Path

from si_whisper_flow import start_ui_server
from whisper_flow_engine import (
    analyze_and_trim_wav_vad,
    create_sample_speech_wav,
    detect_whisper_environment,
    export_srt_subtitles,
    format_dictation_text,
    load_dictionary,
    save_dictionary_term,
)


def _write_silent_wav(path: Path, seconds: float = 1.5, sr: int = 16000) -> None:
    frames = b"\x05\x00" * int(seconds * sr)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(frames)


class SiWhisperFlowTests(unittest.TestCase):
    def test_vad_blocks_silence_hallucination_and_trims_speech(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            td = Path(tmp)
            silent_wav = td / "silent.wav"
            _write_silent_wav(silent_wav)
            s_res = analyze_and_trim_wav_vad(silent_wav, trimmed_out=td / "s_out.wav")
            self.assertTrue(s_res["ok"])
            self.assertFalse(s_res["has_speech"])
            self.assertTrue(s_res["hallucination_blocked"])

            speech_wav = create_sample_speech_wav(td / "speech.wav", duration_sec=2.4)
            v_res = analyze_and_trim_wav_vad(speech_wav, trimmed_out=td / "trimmed.wav")
            self.assertTrue(v_res["ok"])
            self.assertTrue(v_res["has_speech"])
            self.assertFalse(v_res["hallucination_blocked"])
            self.assertGreater(v_res["original_sec"], v_res["trimmed_sec"])
            self.assertTrue(Path(v_res["trimmed_path"]).exists())

    def test_coding_dictionary_spoken_punctuation_and_srt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            td = Path(tmp)
            save_dictionary_term("cube control", "kubectl", custom_home=td)
            dmap = load_dictionary(custom_home=td)
            raw = "um push git hub then run ff mpeg and cube control new line open paren pie torch close paren period"
            cleaned = format_dictation_text(raw, custom_dict=dmap)
            self.assertIn("GitHub", cleaned)
            self.assertIn("FFmpeg", cleaned)
            self.assertIn("kubectl", cleaned)
            self.assertIn("\n(PyTorch).", cleaned)

            srt = export_srt_subtitles([(0.0, 2.5, cleaned)], td / "out.srt")
            txt = Path(srt).read_text(encoding="utf-8")
            self.assertIn("00:00:00,000 --> 00:00:02,500", txt)

    def test_hardware_audit_and_web_studio_endpoints(self) -> None:
        env = detect_whisper_environment()
        self.assertTrue(env["ok"])
        with tempfile.TemporaryDirectory() as tmp:
            td = Path(tmp)
            srv = start_ui_server(port=0, custom_home=td)
            port = srv.server_address[1]
            threading.Thread(target=srv.serve_forever, daemon=True).start()
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/?view=audit", timeout=5) as r:
                    self.assertEqual(r.status, 200)
                    self.assertIn("SI-Whisper-", r.read().decode("utf-8"))

                with urllib.request.urlopen(
                    urllib.request.Request(f"http://127.0.0.1:{port}/api/vad-demo", data=b"", method="POST"),
                    timeout=5,
                ) as r2:
                    self.assertEqual(r2.status, 200)
                    self.assertIn("trimmed_sec", r2.read().decode("utf-8"))
            finally:
                srv.shutdown()
                srv.server_close()


if __name__ == "__main__":
    unittest.main()
