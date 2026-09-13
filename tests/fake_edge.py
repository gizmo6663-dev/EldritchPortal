"""Påsatt edge_tts, så serveren kan testes uten nett til Microsoft."""
import sys, types, asyncio

mod = types.ModuleType("edge_tts")
KALL = []

async def list_voices():
    return [
        {"ShortName": "nb-NO-PernilleNeural", "Locale": "nb-NO",
         "Gender": "Female", "FriendlyName": "Pernille"},
        {"ShortName": "nb-NO-FinnNeural", "Locale": "nb-NO",
         "Gender": "Male", "FriendlyName": "Finn"},
        {"ShortName": "en-US-EmmaNeural", "Locale": "en-US",
         "Gender": "Female", "FriendlyName": "Emma"},
    ]

class Communicate:
    def __init__(self, text, voice, rate="+0%", pitch="+0Hz", volume="+0%"):
        KALL.append({"text": text, "voice": voice, "rate": rate,
                     "pitch": pitch, "volume": volume})
        self.text = text
    async def stream(self):
        yield {"type": "audio", "data": b"ID3-falsk-lyd-" + self.text[:8].encode()}

mod.list_voices = list_voices
mod.Communicate = Communicate
mod.KALL = KALL
sys.modules["edge_tts"] = mod
