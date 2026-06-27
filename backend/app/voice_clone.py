from __future__ import annotations

import uuid
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
USER_VOICES_DIR = BASE_DIR / "user_voices"
GENERATED_AUDIO_DIR = BASE_DIR / "generated_audio"

USER_VOICES_DIR.mkdir(parents=True, exist_ok=True)
GENERATED_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

_chatterbox_model = None
_xtts_model = None
_active_backend: str | None = None


def _safe_extension(filename: str | None) -> str:
    if not filename:
        return ".wav"
    ext = Path(filename).suffix.lower().strip()
    return ext if ext in {".wav", ".mp3", ".m4a", ".ogg", ".flac"} else ".wav"


def _load_chatterbox():
    global _chatterbox_model
    if _chatterbox_model is not None:
        return _chatterbox_model

    try:
        from chatterbox.tts import ChatterboxTTS  # type: ignore
        import torch

        device = "cuda" if torch.cuda.is_available() else "cpu"
        _chatterbox_model = ChatterboxTTS.from_pretrained(device=device)
        print(f"[voice_clone] Using Chatterbox on {device}")
        return _chatterbox_model
    except Exception as e:
        print(f"[voice_clone] Chatterbox unavailable: {e}")
        return None


def _load_xtts():
    global _xtts_model
    if _xtts_model is not None:
        return _xtts_model

    try:
        import torch

        try:
            import transformers.pytorch_utils as hf_pytorch_utils
            if not hasattr(hf_pytorch_utils, "isin_mps_friendly"):
                def isin_mps_friendly(elements, test_elements):
                    return torch.isin(elements, test_elements)
                hf_pytorch_utils.isin_mps_friendly = isin_mps_friendly
        except Exception:
            pass

        from TTS.api import TTS  # type: ignore
        _xtts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        print("[voice_clone] Using XTTS-v2 fallback")
        return _xtts_model
    except Exception as e:
        print(f"[voice_clone] XTTS-v2 unavailable: {e}")
        return None


def _get_backend():
    global _active_backend

    cb = _load_chatterbox()
    if cb is not None:
        _active_backend = "chatterbox"
        return "chatterbox", cb

    xt = _load_xtts()
    if xt is not None:
        _active_backend = "xtts"
        return "xtts", xt

    raise RuntimeError(
        "No local cloned-voice backend is available. "
        "Install one of these:\n"
        "  pip install chatterbox-tts\n"
        "or\n"
        "  pip install TTS"
    )


def clone_voice_elevenlabs(file_bytes: bytes, filename: str, voice_name: str) -> str:
    ext = _safe_extension(filename)
    safe_name = "".join(
        ch for ch in voice_name if ch.isalnum() or ch in {"_", "-"}
    ).strip() or "voice_sample"

    file_path = USER_VOICES_DIR / f"{safe_name}_{uuid.uuid4().hex}{ext}"
    file_path.write_bytes(file_bytes)
    return str(file_path)


def synthesize_with_cloned_voice(voice_id: str, text: str) -> bytes:
    if not text or not text.strip():
        raise ValueError("Text is empty")

    speaker_wav = Path(voice_id)
    if not speaker_wav.exists():
        raise FileNotFoundError(f"Reference voice file not found: {speaker_wav}")

    backend, model = _get_backend()
    output_path = GENERATED_AUDIO_DIR / f"reply_{uuid.uuid4().hex}.wav"

    try:
        if backend == "chatterbox":
            import torchaudio  # type: ignore

            wav = model.generate(
                text.strip(),
                audio_prompt_path=str(speaker_wav),
            )
            torchaudio.save(str(output_path), wav, model.sr)

        elif backend == "xtts":
            model.tts_to_file(
                text=text.strip(),
                speaker_wav=str(speaker_wav),
                language="en",
                file_path=str(output_path),
            )

        return output_path.read_bytes()

    finally:
        try:
            output_path.unlink(missing_ok=True)
        except Exception:
            pass