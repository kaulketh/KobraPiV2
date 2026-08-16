import logging
from dataclasses import dataclass
from time import sleep

import requests

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Gestures:
    neutral: str = "neutral"
    serious: str = "serious"
    calm: str = "calm"
    crying: str = "crying"
    sad: str = "sad"
    cute: str = "cute"
    kiss: str = "kiss"
    love: str = "love"
    love2: str = "love2"
    anime_love: str = "anime_love"
    angry: str = "angry"
    left: str = "left"
    fire: str = "fire"


@dataclass(frozen=True)
class MarqueeMode:
    loop: str = "loop"
    once: str = "once"


class Fjell:
    NOTES = {
        "C4": 262,
        "D4": 294,
        "E4": 330,
        "F4": 349,
        "G4": 392,
        "A4": 440,
        "B4": 494,
        "C5": 523,
        "D5": 587,
        "E5": 659,
        "F5": 698,
        "G5": 784,
        "A5": 880,
        "B5": 988,
        "REST": 0,
    }

    def __init__(
            self,
            host: str = "http://192.168.0.190",
            timeout: float = 3.0,
    ):
        self.host = host.rstrip("/")
        self.timeout = timeout

        self.gesture = Gestures()
        self.mode = MarqueeMode()

        self._session = requests.Session()

    def _post(
            self,
            endpoint: str,
            params: dict | None = None,
    ) -> bool:

        url = f"{self.host}/api/{endpoint}"

        try:
            response = self._session.post(
                url,
                params=params,
                timeout=self.timeout,
            )

            response.raise_for_status()

        except requests.exceptions.Timeout:
            logger.warning("Fjell timeout: %s", url)
            return False

        except requests.exceptions.ConnectionError:
            logger.warning("Fjell nicht erreichbar: %s", self.host)
            return False

        except requests.exceptions.HTTPError as error:
            logger.warning("Fjell HTTP-Fehler: %s", error)
            return False

        except requests.exceptions.RequestException as error:
            logger.warning("Fjell Request fehlgeschlagen: %s", error)
            return False

        return True

    def marquee(
            self,
            text: str,
            mode: str = "once",
    ) -> bool:

        return self._post(
            "marquee",
            params={
                "mode": mode,
                "text": text,
            },
        )

    def emotion(
            self,
            gesture: str,
    ) -> bool:

        return self._post(
            "emotion",
            params={
                "name": gesture,
            },
        )

    def tap(self) -> bool:
        return self._post("tap")

    def double(self) -> bool:
        return self._post("double")

    def sleep(self) -> bool:
        return self._post("sleep")

    def beep(
            self,
            freq_hz: int,
            duration_ms: int,
    ) -> bool:

        return self._post(
            "beep",
            params={
                "f": freq_hz,
                "ms": duration_ms,
            },
        )

    def vibrate(
            self,
            duration_ms: int,
    ) -> bool:

        return self._post(
            "vibrate",
            params={
                "ms": duration_ms,
            },
        )

    def play_note(
            self,
            note: str,
            duration_ms: int,
    ) -> bool:

        note = note.upper()

        if note not in self.NOTES:
            logger.warning("Unbekannte Note: %s", note)
            return False

        frequency = self.NOTES[note]

        if frequency == 0:
            sleep(duration_ms / 1000)
            return True

        return self.beep(
            frequency,
            duration_ms,
        )

    def play(
            self,
            melody: list[tuple[str, float]],
            bpm: int = 120,
            gap: float = 0.1,
    ) -> bool:
        """
        melody:
            ("C4", 1)    Viertelnote
            ("C4", 0.5)  Achtelnote
            ("C4", 2)    Halbe Note
            ("REST", 1)  Pause

        bpm:
            Beats per minute

        gap:
            Anteil der Notendauer als Pause zwischen den Noten
        """

        quarter_ms = 60_000 / bpm

        for note, beats in melody:

            total_duration = quarter_ms * beats

            note_duration = int(
                total_duration * (1 - gap)
            )

            gap_duration = total_duration - note_duration

            if not self.play_note(
                    note,
                    note_duration,
            ):
                return False

            sleep(gap_duration / 1000)

        return True


FJELL = Fjell()
