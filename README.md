# Voice AI Personal Assistant

A minimal real-time voice assistant built with [Pipecat](https://github.com/pipecat-ai/pipecat). You talk to it in the browser in Spanish (Chilean) or English, and it answers out loud.

By default everything runs locally:

| Stage | Service |
|---|---|
| Speech-to-text | Whisper (MLX, on-device) |
| LLM | Qwen 3 4B via Ollama (on-device) — or Claude, OpenAI, Gemini |
| Text-to-speech | Piper (on-device) |
| Transport | SmallWebRTC (browser ↔ bot) |

## Requirements

- Mac with Apple Silicon (the Whisper service uses MLX)
- [uv](https://docs.astral.sh/uv/) — `brew install uv`
- [Ollama](https://ollama.com) for the local LLM — `brew install ollama`
- Chrome

## Setup

```bash
brew services start ollama
ollama pull qwen3:4b-instruct   # or gemma3:1b for a lighter model

cd server
uv sync
cp .env.example .env
```

The first run downloads the Whisper and Piper models (~1 GB).

## Run

```bash
cd server
uv run bot.py
```

Wait for `Uvicorn running on http://localhost:7860`, then open **http://localhost:7860/client**, click Connect, and wait for the greeting before speaking.

## Configuration

All settings live in `server/.env` (see `.env.example`):

| Variable | Default | Purpose |
|---|---|---|
| `BOT_LANGUAGE` | `es` | `es` (Chilean Spanish) or `en`; sets Whisper's language, the voice, and the prompt |
| `LLM_PROVIDER` | `ollama` | `ollama`, `anthropic`, `openai`, `google`, or `auto` (first API key found, else Ollama) |
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `GOOGLE_API_KEY` | — | Only needed for that provider |
| `OLLAMA_MODEL` | `qwen3:4b-instruct` | Local model; `gemma3:1b` is ~2–3× faster and good in English, weaker on Spanish facts |
| `WHISPER_MODEL` | `whisper-large-v3-turbo-q4` | Use `whisper-large-v3-turbo` for better accuracy when the LLM runs in the cloud |
| `PIPER_VOICE` | per language | Defaults: `es_MX-claude-high` / `en_US-lessac-medium`; any Piper voice works |

## Known limitations

- **8 GB Macs:** Whisper and a local LLM compete for memory. Expect 5–10 s per reply; a cloud LLM is much faster.
- **One language per session:** set `BOT_LANGUAGE`; switching languages mid-conversation is not supported. The Spanish voice has a Mexican accent; there is no Chilean Piper voice.
- **Model identity:** local models don't know their own name and may invent one (e.g. Gemma claiming to be PaLM 2).
- **Local LLM quality:** small models make up facts.
- **License:** the `piper-tts` dependency is GPL-3.0, which matters if you distribute the app.
- The UI is Pipecat's built-in test client; a custom React client is planned.

## Troubleshooting

- **No bot audio, transcript only** — the LLM is still loading or not reachable. Check the terminal for `qwen3:4b-instruct loaded` and run `ollama ps`.
- **`Cannot reach Ollama`** — `brew services start ollama`.
- **Port 7860 in use** — another bot is running: `lsof -iTCP:7860 -sTCP:LISTEN`, then stop it with Ctrl+C or `kill <PID>`.
