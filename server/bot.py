"""Voice Lab bot: local Whisper STT -> LLM -> local Piper TTS over SmallWebRTC.

The LLM is local Ollama by default; set LLM_PROVIDER in .env to use Claude,
OpenAI, or Gemini instead. Based on the official Pipecat quickstart. Run with::

    uv run bot.py

Then open http://localhost:7860/client to talk to the bot.
"""

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
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
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


def create_llm(provider: str) -> LLMService:
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
                system_instruction=config.SYSTEM_PROMPT,
            ),
        )

    if provider == "openai":
        from pipecat.services.openai.llm import OpenAILLMService

        llm = OpenAILLMService(
            api_key=os.getenv("OPENAI_API_KEY"),
            settings=OpenAILLMService.Settings(
                **({"model": config.OPENAI_MODEL} if config.OPENAI_MODEL else {}),
                max_completion_tokens=config.LLM_MAX_TOKENS,
                system_instruction=config.SYSTEM_PROMPT,
            ),
        )
    elif provider == "google":
        from pipecat.services.google.llm import GoogleLLMService

        llm = GoogleLLMService(
            api_key=os.getenv("GOOGLE_API_KEY"),
            settings=GoogleLLMService.Settings(
                **({"model": config.GOOGLE_MODEL} if config.GOOGLE_MODEL else {}),
                max_tokens=config.LLM_MAX_TOKENS,
                system_instruction=config.SYSTEM_PROMPT,
            ),
        )
    else:
        from pipecat.services.ollama.llm import OLLamaLLMService

        llm = OLLamaLLMService(
            base_url=config.OLLAMA_BASE_URL,
            settings=OLLamaLLMService.Settings(
                model=config.OLLAMA_MODEL,
                max_tokens=config.LLM_MAX_TOKENS,
                system_instruction=config.SYSTEM_PROMPT,
            ),
        )

    logger.info(f"LLM: {provider} / {llm._settings.model}")
    return llm


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    logger.info("Starting bot")

    stt = WhisperSTTServiceMLX(
        settings=WhisperSTTServiceMLX.Settings(
            model=config.WHISPER_MODEL,
            language=Language.ES,
        ),
    )

    llm = create_llm(LLM_PROVIDER)

    tts = PiperTTSService(
        settings=PiperTTSService.Settings(voice=config.PIPER_VOICE),
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

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
    )

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Client connected")
        # "user" role, since Ollama ignores "developer" messages.
        context.add_message({"role": "user", "content": config.GREETING_INSTRUCTION})
        await task.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected")
        await task.cancel()

    runner = PipelineRunner(handle_sigint=runner_args.handle_sigint)

    await runner.run(task)


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
