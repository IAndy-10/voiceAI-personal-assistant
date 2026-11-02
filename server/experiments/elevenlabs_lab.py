"""Try ElevenLabs endpoints outside the bot pipeline.

Results are saved to experiments/output/ (gitignored). Run from server/::

    uv run experiments/elevenlabs_lab.py design whisper     # 3 previews of a preset voice
    uv run experiments/elevenlabs_lab.py save whisper <generated_voice_id>

Pipecat hides ElevenLabs error messages, so this script prints them as returned.
"""

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

API_URL = "https://api.elevenlabs.io"
OUTPUT_DIR = Path(__file__).parent / "output"

# Voice Design presets. The sample text is spoken in each preview and must be
# 100-1000 characters; Chilean Spanish text helps the model pick the accent.
VOICE_PRESETS = {
    "whisper": {
        "name": "Voice Lab Whisper",
        "description": (
            "A young Chilean woman from Santiago speaking in a soft, breathy whisper, "
            "very close to the microphone. Intimate, calm and gentle, with a natural "
            "Chilean Spanish accent."
        ),
        "text": (
            "Oye, acércate un poquito, que te tengo que contar algo. "
            "Pero bajito, ¿ya? Que nadie más se entere, porque es un secreto entre tú y yo."
        ),
    },
    "dramatic": {
        "name": "Voice Lab Dramatic",
        "description": (
            "A middle-aged Chilean man with a deep, theatrical voice, like a telenovela "
            "narrator. Intense, expressive and dramatic, with clear Chilean Spanish "
            "pronunciation and long pauses."
        ),
        "text": (
            "Y en ese preciso instante, cuando todo parecía perdido, se abrió la puerta. "
            "Nadie lo esperaba. Nadie lo podía creer. ¡Había vuelto, después de tantos años!"
        ),
    },
}


def api_key() -> str:
    load_dotenv(Path(__file__).parent.parent / ".env", override=True)
    key = os.getenv("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("ELEVENLABS_API_KEY is not set in server/.env")
    return key


def post(path: str, body: dict) -> dict:
    """POST JSON to the ElevenLabs API, exiting with the API's own error message on failure."""
    request = urllib.request.Request(
        API_URL + path,
        data=json.dumps(body).encode(),
        headers={"xi-api-key": api_key(), "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"ElevenLabs {e.code}: {e.read().decode()}")


def design(preset: str, model: str) -> None:
    """Generate preview voices for a preset and save them as MP3 files."""
    voice = VOICE_PRESETS[preset]
    result = post(
        "/v1/text-to-voice/design?output_format=mp3_44100_128",
        {"voice_description": voice["description"], "text": voice["text"], "model_id": model},
    )
    OUTPUT_DIR.mkdir(exist_ok=True)
    for i, preview in enumerate(result["previews"], start=1):
        path = OUTPUT_DIR / f"design-{preset}-{i}.mp3"
        path.write_bytes(base64.b64decode(preview["audio_base_64"]))
        print(f"{path}  ({preview['duration_secs']:.1f} s)  {preview['generated_voice_id']}")
    print(f"\nListen, then keep one: uv run experiments/elevenlabs_lab.py save {preset} <id>")


def save(preset: str, generated_voice_id: str) -> None:
    """Save a designed preview as a permanent voice in the ElevenLabs account."""
    voice = VOICE_PRESETS[preset]
    result = post(
        "/v1/text-to-voice",
        {
            "voice_name": voice["name"],
            "voice_description": voice["description"],
            "generated_voice_id": generated_voice_id,
        },
    )
    print(f"Saved {voice['name']!r}: voice_id {result['voice_id']}")
    print(f"Use it with ELEVENLABS_VOICE={result['voice_id']} in server/.env")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)

    design_cmd = commands.add_parser("design", help="generate 3 voice previews for a preset")
    design_cmd.add_argument("preset", choices=VOICE_PRESETS)
    design_cmd.add_argument(
        "--model",
        default="eleven_multilingual_ttv_v2",
        choices=("eleven_multilingual_ttv_v2", "eleven_ttv_v3"),
    )

    save_cmd = commands.add_parser("save", help="save a preview as a permanent voice")
    save_cmd.add_argument("preset", choices=VOICE_PRESETS)
    save_cmd.add_argument("generated_voice_id")

    args = parser.parse_args()
    if args.command == "design":
        design(args.preset, args.model)
    else:
        save(args.preset, args.generated_voice_id)


if __name__ == "__main__":
    main()
