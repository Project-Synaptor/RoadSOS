"""Tests for the voice pipeline: STT, TTS, and webhook integration."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.stt import STTError, transcribe_audio
from app.services.tts import TTSError, synthesize_speech, _SUPPORTED_TTS_LANGUAGES


class TestTranscribeAudio:
    """Test STT transcribe_audio returns (text, language_code) tuple."""

    @pytest.mark.asyncio
    async def test_returns_tuple(self):
        """transcribe_audio should return (transcript, language_code)."""
        mock_audio_resp = MagicMock()
        mock_audio_resp.content = b"fake audio bytes"
        mock_audio_resp.headers = {"content-type": "audio/ogg"}
        mock_audio_resp.raise_for_status = MagicMock()

        mock_stt_resp = MagicMock()
        mock_stt_resp.content = b"fake audio bytes"
        mock_stt_resp.raise_for_status = MagicMock()
        mock_stt_resp.json.return_value = {"text": "accident on highway", "language": "en"}

        with patch("app.services.stt.httpx.AsyncClient") as mock_client:
            instance = AsyncMock()
            instance.get.return_value = mock_audio_resp
            instance.post.return_value = mock_stt_resp
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            mock_client.return_value = instance

            result = await transcribe_audio("https://example.com/audio.ogg")
            assert isinstance(result, tuple)
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_returns_transcript_and_language(self):
        """Should return the transcript text and detected language."""
        mock_audio_resp = MagicMock()
        mock_audio_resp.content = b"fake audio bytes"
        mock_audio_resp.headers = {"content-type": "audio/ogg"}
        mock_audio_resp.raise_for_status = MagicMock()

        mock_stt_resp = MagicMock()
        mock_stt_resp.content = b"fake audio bytes"
        mock_stt_resp.raise_for_status = MagicMock()
        mock_stt_resp.json.return_value = {"text": "accident on highway", "language": "en"}

        with patch("app.services.stt.httpx.AsyncClient") as mock_client:
            instance = AsyncMock()
            instance.get.return_value = mock_audio_resp
            instance.post.return_value = mock_stt_resp
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            mock_client.return_value = instance

            text, lang = await transcribe_audio("https://example.com/audio.ogg")
            assert text == "accident on highway"
            assert lang == "en"

    @pytest.mark.asyncio
    async def test_detects_hindi_from_response(self):
        """Should detect Hindi when STT response contains language field."""
        mock_audio_resp = MagicMock()
        mock_audio_resp.content = b"fake audio bytes"
        mock_audio_resp.headers = {"content-type": "audio/ogg"}
        mock_audio_resp.raise_for_status = MagicMock()

        mock_stt_resp = MagicMock()
        mock_stt_resp.content = b"fake audio bytes"
        mock_stt_resp.raise_for_status = MagicMock()
        mock_stt_resp.json.return_value = {"text": "मुझे मदद चाहिए", "language": "hi"}

        with patch("app.services.stt.httpx.AsyncClient") as mock_client:
            instance = AsyncMock()
            instance.get.return_value = mock_audio_resp
            instance.post.return_value = mock_stt_resp
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            mock_client.return_value = instance

            text, lang = await transcribe_audio("https://example.com/audio.ogg")
            assert text == "मुझे मदद चाहिए"
            assert lang == "hi"

    @pytest.mark.asyncio
    async def test_raises_on_empty_transcript(self):
        """Should raise STTError when transcript is empty."""
        mock_audio_resp = MagicMock()
        mock_audio_resp.content = b"fake audio bytes"
        mock_audio_resp.headers = {"content-type": "audio/ogg"}
        mock_audio_resp.raise_for_status = MagicMock()

        mock_stt_resp = MagicMock()
        mock_stt_resp.content = b"fake audio bytes"
        mock_stt_resp.raise_for_status = MagicMock()
        mock_stt_resp.json.return_value = {"text": ""}

        with patch("app.services.stt.httpx.AsyncClient") as mock_client:
            instance = AsyncMock()
            instance.get.return_value = mock_audio_resp
            instance.post.return_value = mock_stt_resp
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            mock_client.return_value = instance

            with pytest.raises(STTError, match="empty transcript"):
                await transcribe_audio("https://example.com/audio.ogg")


class TestSynthesizeSpeech:
    """Test TTS synthesize_speech with language support."""

    def test_supported_tts_languages(self):
        """Verify the set of TTS-supported languages."""
        assert "en" in _SUPPORTED_TTS_LANGUAGES
        assert "hi" in _SUPPORTED_TTS_LANGUAGES
        assert "bn" in _SUPPORTED_TTS_LANGUAGES
        assert "ta" in _SUPPORTED_TTS_LANGUAGES
        # Odia may not be supported — that's fine, it falls back

    @pytest.mark.asyncio
    async def test_unsupported_language_returns_empty(self):
        """Should return empty string for unsupported languages."""
        result = await synthesize_speech("test text", language_code="xx")
        assert result == ""

    @pytest.mark.asyncio
    async def test_calls_api_for_supported_language(self):
        """Should call MiMo TTS API for supported languages."""
        mock_response = MagicMock()
        mock_response.content = b"fake audio bytes"
        mock_response.raise_for_status = MagicMock()

        with patch("app.services.tts.httpx.AsyncClient") as mock_client:
            instance = AsyncMock()
            instance.post.return_value = mock_response
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            mock_client.return_value = instance

            result = await synthesize_speech("help is on the way", language_code="en")
            assert result != ""
            instance.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_default_language_is_english(self):
        """Default language_code should be 'en'."""
        mock_response = MagicMock()
        mock_response.content = b"fake audio bytes"
        mock_response.raise_for_status = MagicMock()

        with patch("app.services.tts.httpx.AsyncClient") as mock_client:
            instance = AsyncMock()
            instance.post.return_value = mock_response
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            mock_client.return_value = instance

            result = await synthesize_speech("test")
            assert result != ""

    @pytest.mark.asyncio
    async def test_raises_on_api_failure(self):
        """Should raise TTSError on API failure."""
        import httpx

        with patch("app.services.tts.httpx.AsyncClient") as mock_client:
            instance = AsyncMock()
            instance.post.side_effect = httpx.RequestError("connection failed")
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            mock_client.return_value = instance

            with pytest.raises(TTSError, match="request failed"):
                await synthesize_speech("test", language_code="en")


class TestWebhookVoiceFlow:
    """Test webhook handles voice messages with language detection."""

    def test_session_schema_has_language_fields(self):
        """SessionState should have language_code and input_modality."""
        from app.models.schemas import SessionState

        session = SessionState(user_id="test")
        assert session.language_code == "en"
        assert session.input_modality == "text"

    def test_session_language_persists(self):
        """Language fields should be settable."""
        from app.models.schemas import SessionState

        session = SessionState(user_id="test", language_code="hi", input_modality="voice")
        assert session.language_code == "hi"
        assert session.input_modality == "voice"
