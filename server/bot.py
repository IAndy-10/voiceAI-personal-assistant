"""Voice Lab bot: local Whisper STT -> LLM -> local Piper TTS over SmallWebRTC.

The LLM is local Ollama by default; set LLM_PROVIDER in .env to use Claude,
OpenAI, or Gemini instead. Based on the official Pipecat quickstart. Run with::

    uv run bot.py

Then open http://localhost:7860/client to talk to the bot.
"""

import asyncio
import json
import os
import sys
import urllib.error
import urllib.request

from loguru import logger

import config


def warm_up_ollama() -> None:
    """Load the Ollama model before any client connects and keep it in memory.

    Loading takes 20+ seconds on low-memory machines. If that happens on the first
    user turn, each new utterance interrupts the pending request and aborts the load.
    """
    base_url = config.OLLAMA_BASE_URL.removesuffix("/").removesuffix("/v1")
    body = json.dumps({"model": config.OLLAMA_MODEL, "keep_alive": config.OLLAMA_KEEP_ALIVE})
    request = urllib.request.Request(
        f"{base_url}/api/generate",
        data=body.encode(),
        headers={"Content-Type": "application/json"},
    )
    logger.info(f"Loading {config.OLLAMA_MODEL} into Ollama (can take ~30 s)...")
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            response.read()
    except urllib.error.HTTPError as e:
        logger.error(f"Ollama could not load {config.OLLAMA_MODEL}: {e.read().decode()}")
        logger.error(f"Pull it first with: ollama pull {config.OLLAMA_MODEL}")
        sys.exit(1)
    except (urllib.error.URLError, TimeoutError) as e:
        logger.error(f"Cannot reach Ollama at {base_url}: {e}")
        logger.error("Start it with: brew services start ollama")
        sys.exit(1)
    logger.info(f"{config.OLLAMA_MODEL} loaded (kept for {config.OLLAMA_KEEP_ALIVE} when idle)")


LLM_PROVIDER = config.resolve_llm_provider()
if LLM_PROVIDER == "ollama":
    warm_up_ollama()

logger.info("Loading Pipecat components (first run downloads the models)...")
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import LLMRunFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineParams, PipelineWorker, ProcessorUnusablePolicy
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.services.llm_service import LLMService
from pipecat.services.piper.tts import PiperTTSService
from pipecat.services.whisper.stt import WhisperSTTServiceMLX
from pipecat.transcriptions.language import Language
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.workers.runner import WorkerRunner


def create_llm(provider: str, system_prompt: str) -> LLMService:
    """Build the LLM service for the given provider. Provider SDKs are imported lazily."""
    if provider == "anthropic":
        from pipecat.services.anthropic.llm import AnthropicLLMService

        logger.info(f"LLM: anthropic / {config.ANTHROPIC_MODEL}")
        return AnthropicLLMService(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            settings=AnthropicLLMService.Settings(
                model=config.ANTHROPIC_MODEL,
                effort=config.ANTHROPIC_EFFORT,
                max_tokens=config.LLM_MAX_TOKENS,
                system_instruction=system_prompt,
            ),
        )

    if provider == "openai":
        from pipecat.services.openai.llm import OpenAILLMService

        llm = OpenAILLMService(
            api_key=os.getenv("OPENAI_API_KEY"),
            settings=OpenAILLMService.Settings(
                **({"model": config.OPENAI_MODEL} if config.OPENAI_MODEL else {}),
                max_completion_tokens=config.LLM_MAX_TOKENS,
                system_instruction=system_prompt,
            ),
        )
    elif provider == "google":
        from pipecat.services.google.llm import GoogleLLMService

        llm = GoogleLLMService(
            api_key=os.getenv("GOOGLE_API_KEY"),
            settings=GoogleLLMService.Settings(
                **({"model": config.GOOGLE_MODEL} if config.GOOGLE_MODEL else {}),
                max_tokens=config.LLM_MAX_TOKENS,
                system_instruction=system_prompt,
            ),
        )
    else:
        from pipecat.services.ollama.llm import OLLamaLLMService

        llm = OLLamaLLMService(
            base_url=config.OLLAMA_BASE_URL,
            settings=OLLamaLLMService.Settings(
                model=config.OLLAMA_MODEL,
                max_tokens=config.LLM_MAX_TOKENS,
                system_instruction=system_prompt,
            ),
        )

    logger.info(f"LLM: {provider} / {llm._settings.model}")
    return llm


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    # The React client sends {"language": "es" | "en"} in the /start body; /client sends none.
    body = runner_args.body if isinstance(runner_args.body, dict) else {}
    language = config.language_settings(body.get("language"))
    logger.info(f"Starting bot (language: {language.code}, voice: {language.piper_voice})")

    stt = WhisperSTTServiceMLX(
        settings=WhisperSTTServiceMLX.Settings(
            model=config.WHISPER_MODEL,
            language=Language(language.stt_language),
        ),
    )

    llm = create_llm(LLM_PROVIDER, language.system_prompt)

    tts = PiperTTSService(
        settings=PiperTTSService.Settings(voice=language.piper_voice),
    )

    context = LLMContext()
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(vad_analyzer=SileroVADAnalyzer()),
    )

    pipeline = Pipeline(
        [
            transport.input(),  # Transport user input
            stt,
            user_aggregator,  # User responses
            llm,  # LLM
            tts,  # TTS
            transport.output(),  # Transport bot output
            assistant_aggregator,  # Assistant spoken responses
        ]
    )

    worker = PipelineWorker(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
        # Ends the session when the user hasn't spoken for this long (0 disables it).
        idle_timeout_secs=config.IDLE_TIMEOUT_SECS or None,
        # A service that can't recover (e.g. a rejected API key) ends the session;
        # the error has already been sent to the client.
        processor_unusable_policy=ProcessorUnusablePolicy.END,
    )

    async def end_after_max_duration():
        await asyncio.sleep(config.MAX_SESSION_SECS)
        logger.info(f"Session reached the {config.MAX_SESSION_SECS} s limit, ending it")
        await worker.stop_when_done()

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Client connected")
        # "user" role, since Ollama ignores "developer" messages.
        context.add_message({"role": "user", "content": language.greeting})
        await worker.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected")
        await worker.cancel()

    runner = WorkerRunner(handle_sigint=runner_args.handle_sigint)

    max_duration = asyncio.create_task(end_after_max_duration())
    try:
        await runner.run(worker)
    finally:
        max_duration.cancel()


async def bot(runner_args: RunnerArguments):
    """Main bot entry point for the Pipecat runner."""
    transport_params = {
        "webrtc": lambda: TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
        ),
    }

    transport = await create_transport(runner_args, transport_params)

    await run_bot(transport, runner_args)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
