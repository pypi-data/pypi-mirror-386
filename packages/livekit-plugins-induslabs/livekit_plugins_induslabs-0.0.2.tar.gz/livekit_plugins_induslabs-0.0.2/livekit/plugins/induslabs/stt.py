"""IndusLabs Speech‑to‑Text implementation for LiveKit Agents.

This module implements a streaming speech‑to‑text (STT) provider
compatible with the LiveKit Agents framework.  It uses a simple
voice activity detection (VAD) gate to segment incoming audio into
utterances and sends each utterance to the IndusLabs transcription
service over HTTP.  Transcriptions are streamed back from the API
using server‑sent events (SSE) and are converted into
``SpeechEvent`` instances which are passed downstream.

Unlike many STT providers this implementation does not support a
single request for an entire audio buffer; it is intended for
realtime use.  A missing API key will result in a no‑op and no
transcriptions will be returned.
"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
import wave
import weakref
from typing import Optional

import aiohttp
import numpy as np
import webrtcvad

from livekit import rtc
from livekit.agents import (
    DEFAULT_API_CONNECT_OPTIONS,
    APIConnectOptions,
    stt,
)
from livekit.agents.stt import SpeechEvent, SpeechData, SpeechEventType
from livekit.agents.types import NOT_GIVEN, NotGivenOr

from .log import logger

# ---------------------------------------------------------------------------
# Configuration constants.  These values control the voice activity detector
# and the segmentation logic.  Feel free to tune them to your use case.

REMOTE_API_URL = "https://voice.induslabs.io/v1/audio/transcribe"
API_KEY_ENV_VAR = "INDUSLABS_API_KEY"

# WebRTC VAD supports 10, 20, or 30 ms frames.  20 ms is a good balance
# between responsiveness and accuracy.
FRAME_MS = 20

# Aggressiveness of the VAD: 0 = very tolerant of noise, 3 = very strict
VAD_AGGRESSIVENESS = 1

# Minimum voiced duration before speech is considered started and minimum
# silence duration before speech is considered ended (in ms).
SPEECH_START_MS = 100
SPEECH_END_MS = 1_200

# Safety limit on utterance length; if an utterance exceeds this many
# seconds it will be forcibly terminated and sent to the API.
MAX_UTTERANCE_S = 12.0

# RMS energy threshold (normalised to 0‑1 range) used as a quick
# pre‑filter before invoking the VAD.  Frames below this threshold
# are considered silent.
ENERGY_THRESHOLD = 5e-4


class STTOptions:
    """Runtime configuration for the STT stream."""

    def __init__(self, sample_rate: int = 16_000, language: Optional[str] = None) -> None:
        self.sample_rate = sample_rate
        self.language = language


class STT(stt.STT):
    """Realtime streaming speech recogniser for IndusLabs.

    This STT implementation segments incoming audio using a voice
    activity detector and sends each utterance to the IndusLabs
    transcription endpoint.  The responses are streamed back as
    server‑sent events (SSE), allowing partial results to be delivered
    without waiting for the entire utterance.

    Parameters
    ----------
    sample_rate:
        Sample rate of the incoming audio frames.  Must be 8, 16, 32 or
        48 kHz; IndusLabs currently performs best at 16 kHz.
    language:
        Optional language code hint for the recogniser, e.g. "hi" for
        Hindi or "en" for English.  If omitted the service attempts to
        auto‑detect the language.
    """

    def __init__(self, *, sample_rate: int = 16_000, language: Optional[str] = None) -> None:
        super().__init__(capabilities=stt.STTCapabilities(streaming=True, interim_results=True))
        self._opts = STTOptions(sample_rate=sample_rate, language=language)
        # Track active streams without creating strong references
        self._streams = weakref.WeakSet[SpeechStream]()

    @property
    def model(self) -> str:
        return "induslabs-stt-v1"

    @property
    def provider(self) -> str:
        return "IndusLabs"

    def stream(
        self,
        *,
        language: NotGivenOr[str] = NOT_GIVEN,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> "SpeechStream":
        opts = STTOptions(
            sample_rate=self._opts.sample_rate,
            language=None if (language is NOT_GIVEN or not language) else language,
        )
        stream = SpeechStream(stt=self, opts=opts, conn_options=conn_options)
        self._streams.add(stream)
        return stream

    async def _recognize_impl(self, audio: bytes, *, language: Optional[str] = None):
        """Offline recognition is not implemented for IndusLabs STT."""
        raise NotImplementedError(
            "Only streaming mode is supported for the IndusLabs STT plugin."
        )


class SpeechStream(stt.SpeechStream):
    """Process audio frames, segment utterances and send them to the API."""

    def __init__(self, *, stt: STT, opts: STTOptions, conn_options: APIConnectOptions):
        super().__init__(stt=stt, conn_options=conn_options, sample_rate=opts.sample_rate)
        self._opts = opts
        # VAD state
        self._vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)
        self._in_speech = False
        self._voiced_ms = 0
        self._unvoiced_ms = 0
        # Buffers
        self._utterance_buffer_f32: list[float] = []
        self._seconds_in_utterance = 0.0
        # Frame size in samples
        self._frame_samples = int(self._opts.sample_rate * FRAME_MS / 1000)
        self._last_text: Optional[str] = None

    def update_options(self, *, language: Optional[str] = None) -> None:
        """Update the language hint for this stream."""
        self._opts.language = language

    # Helper functions ------------------------------------------------------
    def _int16_to_float32(self, pcm16: np.ndarray) -> np.ndarray:
        return pcm16.astype(np.float32) / 32768.0

    def _rms_energy(self, pcm_f32: np.ndarray) -> float:
        return np.sqrt(np.mean(pcm_f32 ** 2))

    async def _write_wav(self, pcm_f32: np.ndarray) -> str:
        """Persist an utterance into a temporary WAV file for upload."""
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        tmp_path = tmp.name
        tmp.close()
        pcm_clip = np.clip(pcm_f32, -1.0, 1.0)
        pcm16 = (pcm_clip * 32767.0).astype(np.int16)
        with wave.open(tmp_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self._opts.sample_rate)
            wf.writeframes(pcm16.tobytes())
        return tmp_path

    async def _send_utterance(self, pcm_f32: np.ndarray) -> str:
        """Send one utterance to IndusLabs for transcription and return the final text."""
        if pcm_f32.size == 0:
            return ""
        api_key = os.getenv(API_KEY_ENV_VAR)
        if not api_key:
            logger.error("%s not configured; skipping transcription.", API_KEY_ENV_VAR)
            return ""
        tmp_path = await self._write_wav(pcm_f32)
        try:
            async with aiohttp.ClientSession() as session:
                with open(tmp_path, "rb") as wav_file:
                    file_bytes = wav_file.read()
                form = aiohttp.FormData()
                form.add_field(
                    "file",
                    file_bytes,
                    filename="utterance.wav",
                    content_type="audio/wav",
                )
                form.add_field("api_key", api_key)
                if self._opts.language:
                    form.add_field("language", self._opts.language)
                headers = {"Accept": "text/event-stream"}
                async with session.post(
                    REMOTE_API_URL,
                    data=form,
                    headers=headers,
                ) as resp:
                    if resp.status != 200:
                        logger.error(
                            "Remote STT failed %s: %s", resp.status, await resp.text()
                        )
                        return ""
                    final_text = ""
                    buffer = ""
                    async for chunk in resp.content.iter_chunked(1024):
                        if not chunk:
                            continue
                        buffer += chunk.decode("utf-8", errors="ignore")
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            line = line.strip()
                            if not line or line.startswith(":"):
                                continue
                            if not line.startswith("data:"):
                                continue
                            payload = line[5:].strip()
                            if not payload:
                                continue
                            try:
                                msg = json.loads(payload)
                            except json.JSONDecodeError as exc:
                                logger.debug("Failed to decode SSE payload: %s", exc)
                                continue
                            msg_type = msg.get("type")
                            if msg_type == "final":
                                final_text = msg.get("text", "")
                                return final_text
                            if msg_type == "chunk_final" and not final_text:
                                # Provide interim result if a final one hasn't arrived yet
                                final_text = msg.get("text", "")
                    return final_text
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    def _handle_frame_for_eou(self, frame_i16: np.ndarray, frame_f32: np.ndarray) -> Optional[str]:
        """Return None, "START", or "END" based on VAD and energy signals."""
        # Quick energy gate before the more expensive VAD call
        if self._rms_energy(frame_f32) < ENERGY_THRESHOLD:
            is_speech = False
        else:
            is_speech = self._vad.is_speech(frame_i16.tobytes(), self._opts.sample_rate)
        if not self._in_speech:
            if is_speech:
                self._voiced_ms += FRAME_MS
                if self._voiced_ms >= SPEECH_START_MS:
                    self._in_speech = True
                    self._unvoiced_ms = 0
                    return "START"
            else:
                self._voiced_ms = 0
        else:
            if is_speech:
                self._unvoiced_ms = 0
            else:
                self._unvoiced_ms += FRAME_MS
                if self._unvoiced_ms >= SPEECH_END_MS:
                    self._in_speech = False
                    self._voiced_ms = 0
                    self._unvoiced_ms = 0
                    return "END"
        return None

    async def _finalize_and_send_if_any(self) -> None:
        """If the utterance buffer contains data, send it to the API."""
        if not self._utterance_buffer_f32:
            return
        pcm = np.array(self._utterance_buffer_f32, dtype=np.float32)
        self._utterance_buffer_f32.clear()
        self._seconds_in_utterance = 0.0
        text = await self._send_utterance(pcm)
        if text and text != self._last_text:
            self._last_text = text
            ev = SpeechEvent(
                type=SpeechEventType.FINAL_TRANSCRIPT,
                alternatives=[
                    SpeechData(
                        language=self._opts.language or "auto",
                        text=text,
                        confidence=1.0,
                    )
                ],
            )
            logger.info("EOU final transcript: %s", text)
            self._event_ch.send_nowait(ev)

    # Main loop -----------------------------------------------------------
    async def _run(self) -> None:
        carry_i16 = np.zeros((0,), dtype=np.int16)
        while True:
            try:
                item = await self._input_ch.recv()
                if isinstance(item, self._FlushSentinel):
                    # End of stream; emit trailing transcript
                    await self._finalize_and_send_if_any()
                    break
                if not isinstance(item, rtc.AudioFrame):
                    continue
                chunk_i16 = np.frombuffer(item.data, dtype=np.int16)
                if carry_i16.size > 0:
                    chunk_i16 = np.concatenate([carry_i16, chunk_i16])
                    carry_i16 = np.zeros((0,), dtype=np.int16)
                total = chunk_i16.size
                pos = 0
                while pos + self._frame_samples <= total:
                    frame_i16 = chunk_i16[pos : pos + self._frame_samples]
                    pos += self._frame_samples
                    frame_f32 = self._int16_to_float32(frame_i16)
                    marker = self._handle_frame_for_eou(frame_i16, frame_f32)
                    if self._in_speech or marker == "START":
                        self._utterance_buffer_f32.extend(frame_f32.tolist())
                        self._seconds_in_utterance += FRAME_MS / 1000.0
                        if self._seconds_in_utterance >= MAX_UTTERANCE_S:
                            # Force send if utterance is too long
                            await self._finalize_and_send_if_any()
                            self._in_speech = False
                            self._voiced_ms = 0
                            self._unvoiced_ms = 0
                    if marker == "END":
                        await self._finalize_and_send_if_any()
                if pos < total:
                    carry_i16 = chunk_i16[pos:]
            except Exception as e:
                logger.exception("Error in IndusLabs STT stream: %s", e)
                try:
                    await self._finalize_and_send_if_any()
                except Exception:
                    pass
                break