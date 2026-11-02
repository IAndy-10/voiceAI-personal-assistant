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

# --- Session limits ----------------------------------------------------------
# End a session after this long without the user speaking, and after this long in total.
IDLE_TIMEOUT_SECS = float(os.getenv("IDLE_TIMEOUT_SECS", "300"))
MAX_SESSION_SECS = float(os.getenv("MAX_SESSION_SECS", "1800"))

# --- STT / TTS -------------------------------------------------------------
# Multilingual Whisper model; the ".en" models are English-only. The q4 (quantized)
# variant leaves memory for a local LLM on 8 GB machines; use whisper-large-v3-turbo
# for better accuracy when the LLM runs in the cloud.
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "mlx-community/whisper-large-v3-turbo-q4")

# TTS_PROVIDER: piper (default, local) | elevenlabs | elevenlabs-dialogue
# "elevenlabs-dialogue" uses the Eleven v3/v4 models, which perform audio tags such as
# [whispers]; the system prompt then tells the LLM it may write them.
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "piper").strip().lower()
VALID_TTS_PROVIDERS = ("piper", "elevenlabs", "elevenlabs-dialogue")
AUDIO_TAG_PROVIDERS = ("elevenlabs-dialogue",)
ELEVENLABS_KEY = ("ELEVENLABS_API_KEY", "https://elevenlabs.io/app/settings/api-keys")
# Flash v2.5 is ElevenLabs' lowest-latency multilingual model.
ELEVENLABS_MODEL = os.getenv("ELEVENLABS_MODEL", "eleven_flash_v2_5")
# eleven_v4_turbo is the fastest model with audio tags; eleven_v3 sounds best but is slower.
ELEVENLABS_DIALOGUE_MODEL = os.getenv("ELEVENLABS_DIALOGUE_MODEL", "eleven_v4_turbo")

# --- Language ----------------------------------------------------------------
# Each language selects the Whisper language, the default Piper voice, and the prompts.
LANGUAGES = {
    "es": {
        "stt_language": "es",
        # Other Spanish voices: es_MX-ald-medium, es_AR-daniela-high, es_ES-*.
        "piper_voice": "es_MX-claude-high",
        # Any voice ID from the ElevenLabs Voice Library; the multilingual models speak
        # Spanish with any voice, but a native Spanish voice sounds more natural.
        "elevenlabs_voice": "JBFqnCBsd6RMkjVDRZzb",
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
        "audio_tags_prompt": """\
Excepción a la regla de símbolos: puedes usar estas etiquetas de voz, escritas en inglés \
y entre corchetes justo antes de la frase que modifican: [whispers] para susurrar, \
[dramatically] para un tono dramático y [laughs] para reírte. Úsalas solo cuando el \
momento lo pida, como mucho una vez por respuesta, salvo que el usuario te pida \
susurrar o hablar de forma dramática. No uses otras etiquetas.\
""",
        "greeting": "Saluda y preséntate en una sola oración breve.",
    },
    "en": {
        "stt_language": "en",
        # Other English voices: en_US-ryan-high, en_US-amy-medium, en_GB-alan-medium.
        "piper_voice": "en_US-lessac-medium",
        "elevenlabs_voice": "JBFqnCBsd6RMkjVDRZzb",
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
        "audio_tags_prompt": """\
Exception to the symbol rule: you may use these voice tags, in square brackets right \
before the sentence they change: [whispers] to whisper, [dramatically] for a dramatic \
tone, and [laughs] to laugh. Use them only when the moment calls for it, at most once \
per reply, unless the user asks you to whisper or be dramatic. Use no other tags.\
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
ELEVENLABS_VOICE = os.getenv("ELEVENLABS_VOICE") or None


@dataclass(frozen=True)
class LanguageSettings:
    """Everything in the pipeline that depends on the conversation language."""

    code: str
    stt_language: str
    piper_voice: str
    elevenlabs_voice: str
    system_prompt: str
    greeting: str


def language_settings(requested: str | None = None) -> LanguageSettings:
    """Settings for the requested language, falling back to BOT_LANGUAGE."""
    code = (requested or BOT_LANGUAGE).strip().lower()
    if code not in LANGUAGES:
        logger.warning(f"Unknown language {requested!r}; using {BOT_LANGUAGE}")
        code = BOT_LANGUAGE
    language = LANGUAGES[code]
    system_prompt = language["system_prompt"]
    if TTS_PROVIDER in AUDIO_TAG_PROVIDERS:
        system_prompt += "\n\n" + language["audio_tags_prompt"]
    return LanguageSettings(
        code=code,
        stt_language=language["stt_language"],
        piper_voice=PIPER_VOICE or language["piper_voice"],
        elevenlabs_voice=ELEVENLABS_VOICE or language["elevenlabs_voice"],
        system_prompt=system_prompt,
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


def resolve_tts_provider() -> str:
    """Return the TTS provider to use, exiting with an actionable message on bad config."""
    if TTS_PROVIDER not in VALID_TTS_PROVIDERS:
        logger.error(
            f"TTS_PROVIDER={TTS_PROVIDER!r} is invalid. Use one of: {', '.join(VALID_TTS_PROVIDERS)}."
        )
        sys.exit(1)

    if TTS_PROVIDER.startswith("elevenlabs"):
        key_var, url = ELEVENLABS_KEY
        if not os.getenv(key_var):
            logger.error(f"TTS_PROVIDER={TTS_PROVIDER} requires {key_var}. Create one at {url}")
            logger.error("Add it to server/.env, or set TTS_PROVIDER=piper to run locally.")
            sys.exit(1)

    return TTS_PROVIDER
