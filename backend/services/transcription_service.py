"""
Transcription Service for SynkAI.
Extracts the audio track from a video (or audio) file with ffmpeg and transcribes it
locally with faster-whisper, so a recorded meeting flows through the same text-based
pipeline (chunking, RAG, multi-agent analysis) as an uploaded .txt/.pdf/.docx transcript.
"""

import os
import subprocess
import tempfile
from typing import Optional

from backend.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Loaded once per process on first use — faster-whisper model loading is slow
# (and downloads weights on first run), so every subsequent transcription reuses it.
_whisper_model = None


def _get_model():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel

        logger.info(
            f"Loading faster-whisper model '{settings.WHISPER_MODEL_SIZE}' "
            f"(device={settings.WHISPER_DEVICE}, compute_type={settings.WHISPER_COMPUTE_TYPE})..."
        )
        _whisper_model = WhisperModel(
            settings.WHISPER_MODEL_SIZE,
            device=settings.WHISPER_DEVICE,
            compute_type=settings.WHISPER_COMPUTE_TYPE,
        )
    return _whisper_model


class TranscriptionService:
    """
    Service responsible for turning a video or audio meeting recording into plain
    transcript text.
    """

    @classmethod
    def transcribe(cls, media_path: str) -> str:
        """
        Extracts the audio track from `media_path` and transcribes it with Whisper.

        Args:
            media_path: Path to a video or audio file on disk.

        Returns:
            The transcribed text. Downstream services (chunking, RAG, the multi-agent
            pipeline) consume this exactly like text extracted from a .txt/.pdf/.docx file.

        Raises:
            ValueError: If the media file does not exist.
            RuntimeError: If ffmpeg is unavailable, audio extraction fails, or
                transcription fails.
        """
        if not os.path.exists(media_path):
            raise ValueError(f"Media file not found at path: {media_path}")

        with tempfile.TemporaryDirectory() as tmp_dir:
            audio_path = os.path.join(tmp_dir, "audio.wav")
            cls._extract_audio(media_path, audio_path)
            return cls._transcribe_audio(audio_path)

    @staticmethod
    def _extract_audio(media_path: str, audio_path: str) -> None:
        """
        Extracts a 16kHz mono WAV audio track from `media_path` via ffmpeg — the
        sample rate and channel layout faster-whisper expects.
        """
        command = [
            "ffmpeg",
            "-y",
            "-i", media_path,
            "-vn",
            "-ac", "1",
            "-ar", "16000",
            "-f", "wav",
            audio_path,
        ]
        logger.info(f"Extracting audio from '{media_path}' via ffmpeg...")

        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=settings.FFMPEG_TIMEOUT,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(
                "ffmpeg is not installed or not on PATH. Install it (e.g. "
                "`brew install ffmpeg` or `apt install ffmpeg`) to enable video/audio "
                "transcription."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"Audio extraction timed out after {settings.FFMPEG_TIMEOUT}s."
            ) from exc

        if result.returncode != 0 or not os.path.exists(audio_path):
            stderr_tail = result.stderr.decode("utf-8", errors="ignore")[-2000:]
            logger.error(f"ffmpeg failed for '{media_path}': {stderr_tail}")
            raise RuntimeError(
                f"Could not extract audio from '{os.path.basename(media_path)}'. "
                "The file may be corrupted or in an unsupported container."
            )

    @staticmethod
    def _transcribe_audio(audio_path: str) -> str:
        """
        Runs faster-whisper over the extracted audio and joins the recognized segments
        into plain text, one line per segment.
        """
        model = _get_model()
        logger.info(f"Transcribing '{audio_path}' with Whisper...")

        try:
            segments, info = model.transcribe(audio_path, beam_size=settings.WHISPER_BEAM_SIZE)
            lines = [segment.text.strip() for segment in segments if segment.text.strip()]
        except Exception as exc:
            logger.error(f"Whisper transcription failed for '{audio_path}': {exc}", exc_info=True)
            raise RuntimeError(f"Speech-to-text transcription failed: {exc}") from exc

        transcript = "\n".join(lines).strip()

        if not transcript:
            logger.warning(f"No speech detected in '{audio_path}'.")

        detected_language: Optional[str] = getattr(info, "language", None)
        logger.info(
            f"Transcription complete: language='{detected_language or 'unknown'}', "
            f"{len(lines)} segment(s), {len(transcript)} characters."
        )
        return transcript
