from pathlib import Path
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtCore import QUrl


class AudioController:
    def __init__(self, sound_path: Path) -> None:
        self._muted = False
        self._effect: QSoundEffect | None = None
        if sound_path.exists():
            self._effect = QSoundEffect()
            self._effect.setSource(QUrl.fromLocalFile(str(sound_path)))
            self._effect.setVolume(0.8)

    def play(self) -> None:
        if self._muted or self._effect is None:
            return
        self._effect.play()

    def toggle_mute(self) -> None:
        self._muted = not self._muted

    @property
    def muted(self) -> bool:
        return self._muted
