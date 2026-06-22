from pathlib import Path
from unittest.mock import patch
from barkoder.audio import AudioController


class TestAudioController:
    """Test AudioController with mocked QSoundEffect."""

    def test_init_with_nonexistent_file(self):
        """When no sound files exist, _effects is empty."""
        controller = AudioController([Path("/nonexistent/path/bark.wav")])
        assert len(controller._effects) == 0

    @patch("barkoder.audio.QSoundEffect")
    def test_init_with_existing_file(self, mock_sound_effect_class, tmp_path):
        """When sound file exists, QSoundEffect is created and configured."""
        audio_file = tmp_path / "bark.wav"
        audio_file.write_bytes(b"dummy audio data")

        controller = AudioController([audio_file])

        mock_sound_effect_class.assert_called_once()
        mock_instance = mock_sound_effect_class.return_value
        mock_instance.setSource.assert_called_once()
        mock_instance.setVolume.assert_called_once_with(0.8)

    def test_muted_property_default_false(self):
        """Muted property defaults to False."""
        controller = AudioController([Path("/nonexistent/bark.wav")])
        assert controller.muted is False

    def test_toggle_mute(self):
        """toggle_mute switches the muted state."""
        controller = AudioController([Path("/nonexistent/bark.wav")])
        assert controller.muted is False
        controller.toggle_mute()
        assert controller.muted is True
        controller.toggle_mute()
        assert controller.muted is False

    @patch("barkoder.audio.QSoundEffect")
    def test_play_when_muted(self, mock_sound_effect_class, tmp_path):
        """play() does nothing when muted."""
        audio_file = tmp_path / "bark.wav"
        audio_file.write_bytes(b"dummy audio data")

        controller = AudioController([audio_file])
        controller.toggle_mute()
        controller.play()

        mock_sound_effect_class.return_value.play.assert_not_called()

    def test_play_when_no_effects(self):
        """play() does nothing when no effects loaded (file didn't exist)."""
        controller = AudioController([Path("/nonexistent/bark.wav")])
        controller.play()  # should not raise

    @patch("barkoder.audio.QSoundEffect")
    def test_play_when_not_muted_and_effect_exists(self, mock_sound_effect_class, tmp_path):
        """play() calls play() on a random effect when not muted."""
        audio_file = tmp_path / "bark.wav"
        audio_file.write_bytes(b"dummy audio data")

        controller = AudioController([audio_file])
        controller.play()

        mock_sound_effect_class.return_value.play.assert_called_once()

    @patch("barkoder.audio.QSoundEffect")
    def test_play_calls_effect_play(self, mock_sound_effect_class, tmp_path):
        """Calling play() multiple times calls effect.play() each time."""
        audio_file = tmp_path / "bark.wav"
        audio_file.write_bytes(b"dummy audio data")

        controller = AudioController([audio_file])
        controller.play()
        controller.play()

        assert mock_sound_effect_class.return_value.play.call_count == 2

    @patch("barkoder.audio.QSoundEffect")
    def test_multiple_sound_files_loaded(self, mock_sound_effect_class, tmp_path):
        """All existing sound files are loaded as separate effects."""
        files = [tmp_path / f"bark{i}.wav" for i in range(3)]
        for f in files:
            f.write_bytes(b"dummy")

        controller = AudioController(files)
        assert len(controller._effects) == 3
        assert mock_sound_effect_class.call_count == 3
