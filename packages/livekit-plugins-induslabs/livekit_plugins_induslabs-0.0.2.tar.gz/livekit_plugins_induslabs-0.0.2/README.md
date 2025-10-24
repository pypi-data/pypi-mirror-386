# IndusLabs plugin for LiveKit Agents

This repository contains a plugin that enables the
[LiveKit Agents](https://docs.livekit.io/agents/) framework to use
[IndusLabs](https://induslabs.io/) for both text‑to‑speech (TTS) and
speech‑to‑text (STT) services.  By packaging the integration as a
standard Python module you can install it with pip and immediately
register it with your LiveKit agent.

## Features

* **Text‑to‑Speech (TTS)** – synthesize natural‑sounding speech from
  text using IndusLabs models.  Streaming support is provided so that
  audio begins playing as soon as the first bytes arrive.
* **Speech‑to‑Text (STT)** – transcribe speech to text in real time.
  The plugin uses a voice activity detector to segment utterances and
  sends them to the IndusLabs transcription API.
* **Drop‑in installation** – simply run `pip install
  livekit‑plugins‑induslabs` and import the plugin in your agent.  The
  plugin automatically registers itself with the LiveKit plugin
  registry.

## Installation

Ensure you have Python 3.8 or newer installed.  Then run:

```bash
pip install livekit-plugins-induslabs
```

The package depends on the `livekit-agents` library and uses
`aiohttp`, `numpy` and `webrtcvad` under the hood.  These
dependencies will be installed automatically.

You will also need an API key from IndusLabs.  Set the
`INDUSLABS_API_KEY` environment variable before using the plugin or
pass the key explicitly when constructing the `TTS` class.

## Usage

Import the plugin classes and pass them into your `AgentSession`:

```python
from livekit.plugins.induslabs import TTS, STT

# Create instances (reads API key from INDUSLABS_API_KEY if not given)
tts = TTS(voice="Indus-hi-Urvashi")
stt = STT(sample_rate=16000)

session = AgentSession(
    stt=stt,
    tts=tts,
    # ... other components like llm, etc.
)

# run session...
```

### Text‑to‑Speech streaming

```python
response_stream = tts.stream()
response_stream.push("नमस्ते!")
async for event in response_stream:
    # Handle audio bytes from the emitter
```

### Speech‑to‑Text streaming

```python
speech_stream = stt.stream()
async for event in speech_stream:
    if event.type == SpeechEventType.FINAL_TRANSCRIPT:
        print("Final transcript:", event.alternatives[0].text)
```

## Contributing

This project is provided as a reference integration for IndusLabs.  If
you encounter issues or have feature suggestions please open an issue
or submit a pull request on GitHub.