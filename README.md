# Voice AI Personal Assistant

A minimal real-time voice assistant built with [Pipecat](https://github.com/pipecat-ai/pipecat). You talk to it in the browser in Spanish (Chilean), and it answers out loud.

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
ollama pull qwen3:4b-instruct

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
| `LLM_PROVIDER` | `ollama` | `ollama`, `anthropic`, `openai`, `google`, or `auto` (first API key found, else Ollama) |
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `GOOGLE_API_KEY` | — | Only needed for that provider |
| `OLLAMA_MODEL` | `qwen3:4b-instruct` | Local model |
| `WHISPER_MODEL` | `whisper-large-v3-turbo-q4` | Use `whisper-large-v3-turbo` for better accuracy when the LLM runs in the cloud |
| `PIPER_VOICE` | `es_MX-claude-high` | Any Piper voice, e.g. `es_AR-daniela-high` |

## Known limitations

- **8 GB Macs:** Whisper and a local LLM compete for memory. Expect 5–10 s per reply; a cloud LLM is much faster.
- **Spanish only:** speech recognition is fixed to Spanish and the voice has a Mexican accent; there is no Chilean Piper voice.
- **Local LLM quality:** small models make up facts.
- **License:** the `piper-tts` dependency is GPL-3.0, which matters if you distribute the app.
- The UI is Pipecat's built-in test client; a custom React client is planned.

## Troubleshooting

- **No bot audio, transcript only** — the LLM is still loading or not reachable. Check the terminal for `qwen3:4b-instruct loaded` and run `ollama ps`.
- **`Cannot reach Ollama`** — `brew services start ollama`.
- **Port 7860 in use** — another bot is running: `lsof -iTCP:7860 -sTCP:LISTEN`, then stop it with Ctrl+C or `kill <PID>`.
