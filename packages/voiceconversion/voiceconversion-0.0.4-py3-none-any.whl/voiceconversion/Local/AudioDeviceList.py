import logging
import numpy as np
import sounddevice as sd
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal, TypeAlias

ServerAudioDeviceType: TypeAlias = Literal["audioinput", "audiooutput"]

logger = logging.getLogger(__name__)


@dataclass
class ServerAudioDevice:
    index: int = 0
    name: str = ""
    hostAPI: str = ""
    maxInputChannels: int = 0
    maxOutputChannels: int = 0
    default_samplerate: int = 0


def dummy_callback(data: np.ndarray, frames, times, status):
    pass


@lru_cache(maxsize=1)
def checkSamplingRate(deviceId: int, desiredSamplingRate: int, type: ServerAudioDeviceType):
    if type == "input":
        try:
            with sd.InputStream(
                device=deviceId,
                channels=[1, 0],
                callback=dummy_callback,
                dtype="float32",
                samplerate=desiredSamplingRate,
            ):
                pass
            return True
        except Exception as e:  # NOQA
            logger.warning(f"[checkSamplingRate] {e}")
            return False
    else:
        try:
            with sd.OutputStream(
                device=deviceId,
                callback=dummy_callback,
                dtype="float32",
                samplerate=desiredSamplingRate,
            ):
                pass
            return True
        except Exception as e:  # NOQA
            logger.warning(f"[checkSamplingRate] {e}")
            return False


@lru_cache(maxsize=1)
def list_audio_device():
    try:
        audioDeviceList = sd.query_devices()
    except Exception as e:
        logger.exception(e)
        raise e

    inputAudioDeviceList = [d for d in audioDeviceList if d["max_input_channels"] > 0]
    outputAudioDeviceList = [d for d in audioDeviceList if d["max_output_channels"] > 0]
    hostapis = sd.query_hostapis()

    serverAudioInputDevices: list[ServerAudioDevice] = []
    serverAudioOutputDevices: list[ServerAudioDevice] = []
    for d in inputAudioDeviceList:
        serverInputAudioDevice: ServerAudioDevice = ServerAudioDevice(
            index=d["index"],
            name=d["name"],
            hostAPI=hostapis[d["hostapi"]]["name"],
            maxInputChannels=d["max_input_channels"],
            maxOutputChannels=d["max_output_channels"],
            default_samplerate=d["default_samplerate"],
        )
        serverAudioInputDevices.append(serverInputAudioDevice)
    for d in outputAudioDeviceList:
        serverOutputAudioDevice: ServerAudioDevice = ServerAudioDevice(
            index=d["index"],
            name=d["name"],
            hostAPI=hostapis[d["hostapi"]]["name"],
            maxInputChannels=d["max_input_channels"],
            maxOutputChannels=d["max_output_channels"],
            default_samplerate=d["default_samplerate"],
        )
        serverAudioOutputDevices.append(serverOutputAudioDevice)

    return serverAudioInputDevices, serverAudioOutputDevices
