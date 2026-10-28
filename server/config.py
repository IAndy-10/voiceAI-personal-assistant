"""Provider configuration for Voice Lab.

All service choices live here so the pipeline in bot.py does not depend on
any specific provider. Swapping STT/LLM/TTS only requires editing this file
or the environment variables it reads.
"""

import os
import sys
from dataclasses import dataclass

from dotenv import load_dotenv
from loguru import logger

load_dotenv(override=True)

# --- LLM -------------------------------------------------------------------
# LLM_PROVIDER: ollama (default, local) | anthropic | openai | google | auto
# "auto" uses the first provider whose API key is set, in this order,
# and falls back to the local Ollama model when none is set.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").strip().lower()

PROVIDER_KEYS = {
    "anthropic": ("ANTHROPIC_API_KEY", "https://console.anthropic.com/settings/keys"),
    "openai": ("OPENAI_API_KEY", "https://platform.openai.com/api-keys"),
    "google": ("GOOGLE_API_KEY", "https://aistudio.google.com/apikey"),
}
VALID_PROVIDERS = ("ollama", *PROVIDER_KEYS, "auto")

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b-instruct")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
# How long Ollama keeps the model in memory after the last request. Ollama's own
# default (5m) means the first reply after a pause waits for a slow reload.
OLLAMA_KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", "30m")

ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-5-5")
ANTHROPIC_EFFORT = os.getenv("ANTHROPIC_EFFORT", "low")

# Unset means "use Pipecat's default model for that provider".
OPENAI_MODEL = os.getenv("OPENAI_MODEL") or None
GOOGLE_MODEL = os.getenv("GOOGLE_MODEL") or None

LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "400"))

# --- STT / TTS -------------------------------------------------------------
# Multilingual Whisper model; the ".en" models are English-only. The q4 (quantized)
# variant leaves memory for a local LLM on 8 GB machines; use whisper-large-v3-turbo
# for better accuracy when the LLM runs in the cloud.
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "mlx-community/whisper-large-v3-turbo-q4")

# --- Language ----------------------------------------------------------------
# Each language selects the Whisper language, the default Piper voice, and the prompts.
LANGUAGES = {
    "es": {
        "stt_language": "es",
        # Other Spanish voices: es_MX-ald-medium, es_AR-daniela-high, es_ES-*.
        "piper_voice": "es_MX-claude-high",
        "system_prompt": """\
Eres Voice Lab, un asistente de voz amable. Hablas español chileno natural y cercano, \
tratando al usuario de "tú". Puedes usar alguna expresión chilena de vez en cuando, \
sin exagerar.

Todo lo que escribes se convierte en voz, así que:
- Responde en una a tres oraciones cortas, salvo que te pidan más detalle.
- Nunca uses markdown, listas, emojis, URLs ni símbolos especiales.
- Escribe los números y abreviaturas como se pronuncian.

Si la transcripción del usuario está vacía o no tiene sentido, pídele amablemente que \
lo repita. No tienes herramientas ni acceso a internet: nunca digas que realizaste una \
acción externa. Si no sabes algo con certeza, dilo en vez de inventarlo.\
""",
        "greeting": "Saluda y preséntate en una sola oración breve.",
    },
    "en": {
        "stt_language": "en",
        # Other English voices: en_US-ryan-high, en_US-amy-medium, en_GB-alan-medium.
        "piper_voice": "en_US-lessac-medium",
        "system_prompt": """\
You are Voice Lab, a friendly voice assistant. Speak in natural, casual English.

Everything you write is spoken aloud, so:
- Answer in one to three short sentences unless asked for more detail.
- Never use markdown, lists, emoji, URLs, or special symbols.
- Write numbers and abbreviations the way they are pronounced.

If the user's transcript is empty or makes no sense, kindly ask them to repeat it. \
You have no tools or internet access: never claim you performed an external action. \
If you are not sure about something, say so instead of making it up.\
""",
        "greeting": "Say hello and introduce yourself in one short sentence.",
    },
}

# The client picks the language per session; BOT_LANGUAGE is the default when it sends none.
BOT_LANGUAGE = os.getenv("BOT_LANGUAGE", "es").strip().lower()
if BOT_LANGUAGE not in LANGUAGES:
    logger.error(f"BOT_LANGUAGE={BOT_LANGUAGE!r} is invalid. Use one of: {', '.join(LANGUAGES)}.")
    sys.exit(1)

# Overrides the voice for every language when set.
PIPER_VOICE = os.getenv("PIPER_VOICE") or None


@dataclass(frozen=True)
class LanguageSettings:
    """Everything in the pipeline that depends on the conversation language."""

    code: str
    stt_language: str
    piper_voice: str
    system_prompt: str
    greeting: str


def language_settings(requested: str | None = None) -> LanguageSettings:
    """Settings for the requested language, falling back to BOT_LANGUAGE."""
    code = (requested or BOT_LANGUAGE).strip().lower()
    if code not in LANGUAGES:
        logger.warning(f"Unknown language {requested!r}; using {BOT_LANGUAGE}")
        code = BOT_LANGUAGE
    language = LANGUAGES[code]
    return LanguageSettings(
        code=code,
        stt_language=language["stt_language"],
        piper_voice=PIPER_VOICE or language["piper_voice"],
        system_prompt=language["system_prompt"],
        greeting=language["greeting"],
    )


def resolve_llm_provider() -> str:
    """Return the LLM provider to use, exiting with an actionable message on bad config."""
    if LLM_PROVIDER not in VALID_PROVIDERS:
        logger.error(
            f"LLM_PROVIDER={LLM_PROVIDER!r} is invalid. Use one of: {', '.join(VALID_PROVIDERS)}."
        )
        sys.exit(1)

    if LLM_PROVIDER == "auto":
        for provider, (key_var, _) in PROVIDER_KEYS.items():
            if os.getenv(key_var):
                logger.info(f"LLM_PROVIDER=auto: found {key_var}, using {provider}")
                return provider
        logger.info("LLM_PROVIDER=auto: no API keys found, using local ollama")
        return "ollama"

    if LLM_PROVIDER in PROVIDER_KEYS:
        key_var, url = PROVIDER_KEYS[LLM_PROVIDER]
        if not os.getenv(key_var):
            logger.error(f"LLM_PROVIDER={LLM_PROVIDER} requires {key_var}. Create one at {url}")
            logger.error("Add it to server/.env, or set LLM_PROVIDER=ollama to run locally.")
            sys.exit(1)

    return LLM_PROVIDER
