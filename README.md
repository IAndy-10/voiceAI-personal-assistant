# Voice AI Personal Assistant

A minimal real-time voice assistant built with [Pipecat](https://github.com/pipecat-ai/pipecat). You pick Spanish (Chilean) or English in the browser, talk to it, and it answers out loud.

By default everything runs locally:

| Stage | Service |
|---|---|
| Speech-to-text | Whisper (MLX, on-device) |
| LLM | Qwen 3 4B via Ollama (on-device) — or Claude, OpenAI, Gemini |
| Text-to-speech | Piper (on-device) |
| Transport | SmallWebRTC (browser ↔ bot) |
| Client | React + TypeScript + Tailwind (Vite) |

## Requirements

- Mac with Apple Silicon (the Whisper service uses MLX)
- [uv](https://docs.astral.sh/uv/) — `brew install uv`
- [Ollama](https://ollama.com) for the local LLM — `brew install ollama`
- Node.js 22+ for the client
- Chrome

## Setup

```bash
brew services start ollama
ollama pull qwen3:4b-instruct   # or gemma3:1b for a lighter model

cd server
uv sync
cp .env.example .env

cd ../client
npm install
```

The first run downloads the Whisper and Piper models (~1 GB).

## Run

Use two terminals:

```bash
cd server && uv run bot.py    # bot on http://localhost:7860
cd client && npm run dev      # app on http://localhost:5173
```

Wait for `Uvicorn running on http://localhost:7860`, then open **http://localhost:5173**, pick English or Español, click Start conversation, allow the microphone, and wait for the greeting before speaking. The language is locked while a session is running; end it to switch.

Pipecat's built-in test UI is still available at http://localhost:7860/client (it uses `BOT_LANGUAGE`).

| Port | Process |
|---|---|
| 5173 | Vite dev server (proxies `/api/*` to the bot) |
| 7860 | Pipecat bot |
| 11434 | Ollama |

## Checks

```bash
cd server && uv run pytest && uv run ruff check .
cd client && npm run build && npm run check-bundle   # build fails on type errors; check-bundle fails if an API key is in dist/
```

## Configuration

All settings live in `server/.env` (see `.env.example`):

| Variable | Default | Purpose |
|---|---|---|
| `BOT_LANGUAGE` | `es` | Default language when the client sends none (e.g. `/client`): `es` (Chilean Spanish) or `en` |
| `LLM_PROVIDER` | `ollama` | `ollama`, `anthropic`, `openai`, `google`, or `auto` (first API key found, else Ollama) |
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `GOOGLE_API_KEY` | — | Only needed for that provider |
| `OLLAMA_MODEL` | `qwen3:4b-instruct` | Local model; `gemma3:1b` is ~2–3× faster and good in English, weaker on Spanish facts |
| `WHISPER_MODEL` | `whisper-large-v3-turbo-q4` | Use `whisper-large-v3-turbo` for better accuracy when the LLM runs in the cloud |
| `PIPER_VOICE` | per language | Defaults: `es_MX-claude-high` / `en_US-lessac-medium`; any Piper voice works |
| `IDLE_TIMEOUT_SECS` | `300` | End the session after this long without the user speaking; `0` disables it |
| `MAX_SESSION_SECS` | `1800` | End the session after this long in total (**untested**) |

## Known limitations

- **8 GB Macs:** Whisper and a local LLM compete for memory. Expect 5–10 s per reply; a cloud LLM is much faster.
- **One language per session:** pick it before starting; switching mid-conversation is not supported. The Spanish voice has a Mexican accent; there is no Chilean Piper voice.
- **Model identity:** local models don't know their own name and may invent one (e.g. Gemma claiming to be PaLM 2).
- **Local LLM quality:** small models make up facts.
- **License:** the `piper-tts` dependency is GPL-3.0, which matters if you distribute the app.
- **Session limits:** the idle timeout is tested; the `MAX_SESSION_SECS` timer is implemented but untested.
- Tested on desktop Chrome only.

## Troubleshooting

- **No bot audio, transcript only** — the LLM is still loading or not reachable. Check the terminal for `qwen3:4b-instruct loaded` and run `ollama ps`.
- **`Cannot reach Ollama`** — `brew services start ollama`.
- **"Could not reach the voice bot"** — start the bot (`cd server && uv run bot.py`) and click Retry.
- **Stuck on Connecting** — Chrome is waiting for microphone permission; allow it in the address bar.
- **Port 7860 in use** — another bot is running: `lsof -iTCP:7860 -sTCP:LISTEN`, then stop it with Ctrl+C or `kill <PID>`.
