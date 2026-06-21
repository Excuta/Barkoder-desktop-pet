import sys
import pytest

if sys.platform != "win32":
    pytest.skip("Windows-only", allow_module_level=True)

from unittest.mock import MagicMock, patch
from barkoder.startup import StartupManager

REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "Barkoder"


def test_enable_writes_registry():
    with patch("winreg.OpenKey") as mock_open, \
         patch("winreg.SetValueEx") as mock_set:
        mock_open.return_value.__enter__ = lambda s: s
        mock_open.return_value.__exit__ = MagicMock(return_value=False)
        sm = StartupManager(APP_NAME)
        sm.enable("C:\\fake\\barkoder.exe")
        mock_set.assert_called_once()


def test_disable_deletes_registry():
    with patch("winreg.OpenKey") as mock_open, \
         patch("winreg.DeleteValue") as mock_del:
        mock_open.return_value.__enter__ = lambda s: s
        mock_open.return_value.__exit__ = MagicMock(return_value=False)
        sm = StartupManager(APP_NAME)
        sm.disable()
        mock_del.assert_called_once()


def test_is_enabled_true():
    with patch("winreg.OpenKey") as mock_open, \
         patch("winreg.QueryValueEx") as mock_query:
        mock_open.return_value.__enter__ = lambda s: s
        mock_open.return_value.__exit__ = MagicMock(return_value=False)
        mock_query.return_value = ("C:\\fake\\barkoder.exe", 1)
        sm = StartupManager(APP_NAME)
        assert sm.is_enabled() is True


def test_is_enabled_false():
    with patch("winreg.OpenKey") as mock_open, \
         patch("winreg.QueryValueEx") as mock_query:
        mock_open.return_value.__enter__ = lambda s: s
        mock_open.return_value.__exit__ = MagicMock(return_value=False)
        mock_query.side_effect = FileNotFoundError
        sm = StartupManager(APP_NAME)
        assert sm.is_enabled() is False


def test_disable_ignores_missing_key():
    with patch("winreg.OpenKey") as mock_open:
        mock_open.side_effect = FileNotFoundError
        sm = StartupManager(APP_NAME)
        # Should not raise
        sm.disable()
