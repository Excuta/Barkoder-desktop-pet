import logging
import random
from pathlib import Path
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtCore import QUrl

_log = logging.getLogger("barkoder.audio")


class AudioController:
    def __init__(self, sound_paths: list[Path]) -> None:
        self._muted = False
        self._effects: list[QSoundEffect] = []
        for path in sound_paths:
            if path.exists():
                effect = QSoundEffect()
                effect.setSource(QUrl.fromLocalFile(str(path)))
                effect.setVolume(0.8)
                self._effects.append(effect)
        if not self._effects:
            _log.warning("audio: no sound files loaded — bark will be silent")

    def play(self) -> None:
        if self._muted:
            return
        if not self._effects:
            _log.debug("audio: play() called but no effects loaded")
            return
        random.choice(self._effects).play()
        _log.debug("audio: played bark sound (%d available)", len(self._effects))

    def toggle_mute(self) -> None:
        self._muted = not self._muted

    @property
    def muted(self) -> bool:
        return self._muted
