"""Configuration validation: bad settings fail with a clear message, languages fall back."""

import pytest

import config


@pytest.fixture(autouse=True)
def no_api_keys(monkeypatch):
    for key_var, _ in config.PROVIDER_KEYS.values():
        monkeypatch.delenv(key_var, raising=False)
    monkeypatch.setattr(config, "BOT_LANGUAGE", "es")
    monkeypatch.setattr(config, "PIPER_VOICE", None)


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
