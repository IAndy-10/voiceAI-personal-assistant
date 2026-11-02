# Voice AI Personal Assistant

A minimal real-time voice assistant built with [Pipecat](https://github.com/pipecat-ai/pipecat). You pick Spanish (Chilean) or English in the browser, talk to it, and it answers out loud.

By default everything runs locally:

| Stage | Service |
|---|---|
| Speech-to-text | Whisper (MLX, on-device) |
| LLM | Qwen 3 4B via Ollama (on-device) — or Claude, OpenAI, Gemini |
| Text-to-speech | Piper (on-device) — or ElevenLabs |
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

### Optional: ElevenLabs voices

For more natural voices than Piper, use ElevenLabs as the TTS provider (cloud, billed per character):

1. Create an API key at https://elevenlabs.io/app/settings/api-keys. It needs the text-to-speech permission.
2. In `server/.env`, set `TTS_PROVIDER=elevenlabs` and `ELEVENLABS_API_KEY=...`.
3. Restart the bot (`.env` is only read at startup). The log should show `TTS: elevenlabs / eleven_flash_v2_5 / <voice ID>`.

The default voice is George (`JBFqnCBsd6RMkjVDRZzb`). To change it, set `ELEVENLABS_VOICE` to a voice ID from the ElevenLabs website. On the free plan only the default voices and voices you create yourself work; Voice Library voices need a paid plan.

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
| `TTS_PROVIDER` | `piper` | `piper` (local) or `elevenlabs` (cloud, streaming) |
| `ELEVENLABS_API_KEY` | — | Only needed when `TTS_PROVIDER=elevenlabs` |
| `ELEVENLABS_MODEL` | `eleven_flash_v2_5` | ElevenLabs' lowest-latency multilingual model |
| `ELEVENLABS_VOICE` | `JBFqnCBsd6RMkjVDRZzb` | Voice ID for every language; the free plan can't use Voice Library voices |
| `IDLE_TIMEOUT_SECS` | `300` | End the session after this long without the user speaking; `0` disables it |
| `MAX_SESSION_SECS` | `1800` | End the session after this long in total (**untested**) |

## Known limitations

- **8 GB Macs:** Whisper and a local LLM compete for memory. Expect 5–10 s per reply; a cloud LLM is much faster.
- **One language per session:** pick it before starting; switching mid-conversation is not supported. The Spanish Piper voice has a Mexican accent; there is no Chilean Piper voice. With ElevenLabs, the default voice speaks Spanish with an English accent; pick a Spanish voice with `ELEVENLABS_VOICE`.
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
- **Port 7860 in use** — another bot is running: `lsof -iTCP:7860 -sTCP:LISTEN`, then stop it with Ctrl+C or `kill <PID>`. If the process is `com.docker.backend`, a Docker container publishes the port: find it with `docker ps --filter publish=7860` and `docker stop` it, or run this bot with `uv run bot.py --port 7861` and point the proxy in `client/vite.config.ts` at it.
- **`TTS context ... completed with no audio`** (ElevenLabs) — ElevenLabs rejected the request, usually because of the voice: a Voice Library voice on the free plan, or a voice ID that doesn't exist. Remove `ELEVENLABS_VOICE` to use the default voice. Pipecat doesn't log ElevenLabs' actual error message.
- **Still hearing the Piper voice** — check that `TTS_PROVIDER=elevenlabs` isn't commented out in `server/.env`, then restart the bot. Clearing the browser cache doesn't help; the voice comes from the server.
