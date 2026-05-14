"""Tests for the language detection service."""

from app.services.language import (
    LANGUAGE_CODES,
    _detect_explicit_command,
    detect_language_from_stt_response,
    detect_language_from_text,
    get_language_name,
    is_supported,
)


class TestDetectLanguageFromText:
    """Test script-based and keyword-based language detection."""

    def test_english_returns_en(self):
        assert detect_language_from_text("There has been an accident") == "en"

    def test_empty_text_returns_en(self):
        assert detect_language_from_text("") == "en"

    def test_none_like_empty_returns_en(self):
        assert detect_language_from_text("   ") == "en"

    def test_hindi_devanagari_script(self):
        assert detect_language_from_text("मुझे मदद चाहिए दुर्घटना हो गई") == "hi"

    def test_bengali_script(self):
        assert detect_language_from_text("আমাকে সাহায্য করুন দুর্ঘটনা হয়েছে") == "bn"

    def test_odia_script(self):
        assert detect_language_from_text("ମୋତେ ସାହାଯ୍ୟ ଦରକାର ଦୁର୍ଘଟଣା ହୋଇଛି") == "or"

    def test_tamil_script(self):
        assert detect_language_from_text("எனக்கு உதவி வேண்டும் விபத்து நடந்தது") == "ta"

    def test_telugu_script(self):
        assert detect_language_from_text("నాకు సహాయం కావాలి ప్రమాదం జరిగింది") == "te"

    def test_kannada_script(self):
        assert detect_language_from_text("ನನಗೆ ಸಹಾಯ ಬೇಕು ಅಪಘಾತ ಆಗಿದೆ") == "kn"

    def test_malayalam_script(self):
        assert detect_language_from_text("എനിക്ക് സഹായം വേണം അപകടം സംഭവിച്ചു") == "ml"

    def test_hindi_keyword_fallback(self):
        assert detect_language_from_text("hindi mein madad karo") == "hi"

    def test_bengali_keyword_fallback(self):
        assert detect_language_from_text("bangla shahajjo koro") == "bn"

    def test_tamil_keyword_fallback(self):
        assert detect_language_from_text("tamil udavi venum") == "ta"

    def test_telugu_keyword_fallback(self):
        assert detect_language_from_text("telugu sahayam kavali") == "te"

    def test_kannada_keyword_fallback(self):
        assert detect_language_from_text("kannada sahayam beku") == "kn"

    def test_malayalam_keyword_fallback(self):
        assert detect_language_from_text("malayalam sahayam venam") == "ml"

    def test_odia_keyword_fallback(self):
        assert detect_language_from_text("odia sahayata darkar") == "or"


class TestDetectExplicitCommand:
    """Test explicit language command parsing."""

    def test_hindi_command(self):
        assert detect_language_from_text("hindi mein boliye") == "hi"

    def test_hindi_command_speak(self):
        assert detect_language_from_text("speak in Hindi") == "hi"

    def test_tamil_command(self):
        assert detect_language_from_text("speak in Tamil") == "ta"

    def test_bengali_command(self):
        assert detect_language_from_text("speak in Bengali") == "bn"

    def test_telugu_command(self):
        assert detect_language_from_text("speak in Telugu") == "te"

    def test_kannada_command(self):
        assert detect_language_from_text("speak in Kannada") == "kn"

    def test_malayalam_command(self):
        assert detect_language_from_text("speak in Malayalam") == "ml"

    def test_odia_command(self):
        assert detect_language_from_text("speak in Odia") == "or"

    def test_no_command_returns_none(self):
        assert _detect_explicit_command("there has been an accident") is None


class TestDetectLanguageFromSTTResponse:
    """Test language extraction from MiMo STT response."""

    def test_language_field_present(self):
        resp = {"text": "some transcript", "language": "hi"}
        assert detect_language_from_stt_response(resp) == "hi"

    def test_detected_language_field(self):
        resp = {"text": "some transcript", "detected_language": "ta"}
        assert detect_language_from_stt_response(resp) == "ta"

    def test_unknown_language_falls_back_to_text(self):
        resp = {"text": "मुझे मदद चाहिए", "language": "xx"}
        assert detect_language_from_stt_response(resp) == "hi"

    def test_no_language_field_uses_text(self):
        resp = {"text": "ஆமாம் விபத்து நடந்தது"}
        assert detect_language_from_stt_response(resp) == "ta"

    def test_empty_response_defaults_to_en(self):
        resp = {"text": ""}
        assert detect_language_from_stt_response(resp) == "en"


class TestLanguageCodes:
    """Test LANGUAGE_CODES constant and helper functions."""

    def test_all_8_languages_present(self):
        expected = {"en", "hi", "bn", "or", "ta", "te", "kn", "ml"}
        assert set(LANGUAGE_CODES.keys()) == expected

    def test_get_language_name(self):
        assert get_language_name("hi") == "Hindi"
        assert get_language_name("en") == "English"
        assert get_language_name("unknown") == "English"

    def test_is_supported(self):
        assert is_supported("en") is True
        assert is_supported("hi") is True
        assert is_supported("xx") is False
