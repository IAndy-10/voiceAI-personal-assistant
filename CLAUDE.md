# CLAUDE.md

Minimal real-time voice assistant (Chilean Spanish or English, chosen per session) built on Pipecat. Learning project: keep the architecture small.

## Layout

- `server/bot.py` — Pipecat pipeline: SmallWebRTC in → Whisper (MLX) STT → LLM → Piper TTS → out. Entry point uses Pipecat's runner, which also serves the test UI at `/client`.
- `server/config.py` — all provider choices, per-language settings (`LANGUAGES`, `language_settings()`), and `.env` validation. Swapping providers should only touch this file and `create_llm()` in `bot.py`.
- `server/tests/` — pytest config validation tests.
- `client/` — React + TypeScript + Tailwind v4 (Vite). `src/hooks/useVoiceSession.ts` owns all Pipecat client logic; components only render.
- The client sends the language in the start body: `startBotAndConnect({ endpoint: '/api/start', requestData: { body: { language } } })`. The bot reads it from `runner_args.body`.

## Commands

Server (run in `server/`):

```bash
uv sync                 # install dependencies
uv run bot.py           # start on http://localhost:7860 (test UI at /client)
uv run pytest           # tests
uv run ruff check .     # lint
uv run ruff format .    # format
```

Client (run in `client/`):

```bash
npm install
npm run dev             # http://localhost:5173, proxies /api/* to :7860
npm run build           # tsc --noEmit + vite build
npm run check-bundle    # fail if dist/ contains an API key
```

## Rules

- Never commit `server/.env` or print its contents; it may hold API keys.
- Before starting the bot for a test, check that the user isn't already running one: `lsof -iTCP:7860 -sTCP:LISTEN`. Never `pkill` a bot you did not start.
- The runner serves `POST /start` and `/sessions/{id}/api/offer` (no `/api` prefix); the Vite proxy strips `/api`. Don't add custom routes.
- Pin npm packages exactly (`npm install --save-exact`); `@pipecat-ai/*` client versions should match the server's release line.
- Adding or removing hooks in `useVoiceSession` breaks React Fast Refresh mid-session (blank page); reload the page.
- Pipecat changes quickly. `pipecat-ai` is pinned in `pyproject.toml`; verify imports and parameters against the docs or the installed package for that version, not memory.
- Configure Pipecat services with `settings=Service.Settings(...)`. Constructor args like `model=`, `params=`, and `voice_id=` are deprecated.
- Don't pass `model=None` in Settings — it overrides the service default. Omit the field instead.
- The Whisper module imports `faster_whisper` even for the MLX class, so both `whisper` and `mlx-whisper` extras are required.
- Ollama: `bot.py` pre-loads the model at startup with a long `keep_alive`. Without that, the first turn waits for a 20+ s load, and every user utterance cancels and restarts it.
- Use `qwen3:4b-instruct`, not `qwen3:4b`. The base model always "thinks", and disabling thinking leaks reasoning into the spoken reply.
- Ollama ignores `developer` role messages; use `user` for injected instructions.
- Everything the LLM writes is spoken: keep the system prompt asking for short replies with no markdown, lists, or emoji.
- The dev machine is an 8 GB M1. Whisper + local LLM cause memory swapping; measure latency before and after changes.

## Commits

Conventional style: `<type>: <description>` with types `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`.
