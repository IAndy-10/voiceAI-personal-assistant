"""Configuration validation: bad settings fail with a clear message, languages fall back."""

import pytest

import config


@pytest.fixture(autouse=True)
def no_api_keys(monkeypatch):
    for key_var, _ in config.PROVIDER_KEYS.values():
        monkeypatch.delenv(key_var, raising=False)
    monkeypatch.setattr(config, "BOT_LANGUAGE", "es")
    monkeypatch.delenv(config.ELEVENLABS_KEY[0], raising=False)
    monkeypatch.setattr(config, "PIPER_VOICE", None)
    monkeypatch.setattr(config, "ELEVENLABS_VOICE", None)
    monkeypatch.setattr(config, "TTS_PROVIDER", "piper")


def test_invalid_provider_exits(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "nope")
    with pytest.raises(SystemExit):
        config.resolve_llm_provider()


def test_cloud_provider_without_key_exits(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "anthropic")
    with pytest.raises(SystemExit):
        config.resolve_llm_provider()


def test_cloud_provider_with_key(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    assert config.resolve_llm_provider() == "anthropic"


def test_auto_falls_back_to_ollama(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "auto")
    assert config.resolve_llm_provider() == "ollama"


def test_auto_picks_first_key(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "auto")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    assert config.resolve_llm_provider() == "openai"


def test_invalid_tts_provider_exits(monkeypatch):
    monkeypatch.setattr(config, "TTS_PROVIDER", "nope")
    with pytest.raises(SystemExit):
        config.resolve_tts_provider()


def test_elevenlabs_without_key_exits(monkeypatch):
    monkeypatch.setattr(config, "TTS_PROVIDER", "elevenlabs")
    with pytest.raises(SystemExit):
        config.resolve_tts_provider()


def test_elevenlabs_dialogue_without_key_exits(monkeypatch):
    monkeypatch.setattr(config, "TTS_PROVIDER", "elevenlabs-dialogue")
    with pytest.raises(SystemExit):
        config.resolve_tts_provider()


def test_elevenlabs_with_key(monkeypatch):
    monkeypatch.setattr(config, "TTS_PROVIDER", "elevenlabs")
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key")
    assert config.resolve_tts_provider() == "elevenlabs"


@pytest.mark.parametrize(
    ("requested", "code", "voice"),
    [
        ("en", "en", "en_US-lessac-medium"),
        ("es", "es", "es_MX-claude-high"),
        (" EN ", "en", "en_US-lessac-medium"),
        (None, "es", "es_MX-claude-high"),
        ("fr", "es", "es_MX-claude-high"),
    ],
)
def test_language_settings(requested, code, voice):
    language = config.language_settings(requested)
    assert language.code == code
    assert language.stt_language == code
    assert language.piper_voice == voice
    assert language.system_prompt == config.LANGUAGES[code]["system_prompt"]


def test_default_language_from_env(monkeypatch):
    monkeypatch.setattr(config, "BOT_LANGUAGE", "en")
    assert config.language_settings(None).code == "en"


def test_piper_voice_override(monkeypatch):
    monkeypatch.setattr(config, "PIPER_VOICE", "en_US-ryan-high")
    assert config.language_settings("es").piper_voice == "en_US-ryan-high"


def test_elevenlabs_voice_override(monkeypatch):
    monkeypatch.setattr(config, "ELEVENLABS_VOICE", "custom-voice-id")
    assert config.language_settings("es").elevenlabs_voice == "custom-voice-id"


@pytest.mark.parametrize("code", ["es", "en"])
def test_audio_tags_only_with_dialogue_tts(monkeypatch, code):
    tags_prompt = config.LANGUAGES[code]["audio_tags_prompt"]
    assert tags_prompt not in config.language_settings(code).system_prompt
    monkeypatch.setattr(config, "TTS_PROVIDER", "elevenlabs-dialogue")
    assert config.language_settings(code).system_prompt.endswith(tags_prompt)
