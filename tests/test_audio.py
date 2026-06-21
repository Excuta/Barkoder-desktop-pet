import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from barkoder.audio import AudioController


class TestAudioController:
    """Test AudioController with mocked QSoundEffect."""

    def test_init_with_nonexistent_file(self):
        """When sound file doesn't exist, _effect is None."""
        controller = AudioController(Path("/nonexistent/path/bark.wav"))
        assert controller._effect is None

    @patch("barkoder.audio.QSoundEffect")
    def test_init_with_existing_file(self, mock_sound_effect_class, tmp_path):
        """When sound file exists, QSoundEffect is created and configured."""
        # Create a dummy file
        audio_file = tmp_path / "bark.wav"
        audio_file.write_bytes(b"dummy audio data")

        controller = AudioController(audio_file)

        # Verify QSoundEffect was instantiated
        mock_sound_effect_class.assert_called_once()
        mock_instance = mock_sound_effect_class.return_value

        # Verify setSource was called with the file
        mock_instance.setSource.assert_called_once()
        # Verify setVolume was called
        mock_instance.setVolume.assert_called_once_with(0.8)

    def test_muted_property_default_false(self):
        """Muted property defaults to False."""
        controller = AudioController(Path("/nonexistent/bark.wav"))
        assert controller.muted is False

    def test_toggle_mute(self):
        """toggle_mute switches the muted state."""
        controller = AudioController(Path("/nonexistent/bark.wav"))
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

        controller = AudioController(audio_file)
        controller.toggle_mute()  # mute it

        controller.play()

        mock_instance = mock_sound_effect_class.return_value
        mock_instance.play.assert_not_called()

    @patch("barkoder.audio.QSoundEffect")
    def test_play_when_effect_is_none(self, mock_sound_effect_class):
        """play() does nothing when _effect is None (file didn't exist)."""
        controller = AudioController(Path("/nonexistent/bark.wav"))
        controller.play()  # should not raise

        # No QSoundEffect was created, so nothing to call play on
        mock_sound_effect_class.assert_not_called()

    @patch("barkoder.audio.QSoundEffect")
    def test_play_when_not_muted_and_effect_exists(self, mock_sound_effect_class, tmp_path):
        """play() calls _effect.play() when not muted and effect exists."""
        audio_file = tmp_path / "bark.wav"
        audio_file.write_bytes(b"dummy audio data")

        controller = AudioController(audio_file)
        controller.play()

        mock_instance = mock_sound_effect_class.return_value
        mock_instance.play.assert_called_once()

    @patch("barkoder.audio.QSoundEffect")
    def test_play_calls_effect_play(self, mock_sound_effect_class, tmp_path):
        """Calling play() multiple times calls _effect.play() each time."""
        audio_file = tmp_path / "bark.wav"
        audio_file.write_bytes(b"dummy audio data")

        controller = AudioController(audio_file)
        controller.play()
        controller.play()

        mock_instance = mock_sound_effect_class.return_value
        assert mock_instance.play.call_count == 2
