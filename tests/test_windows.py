import pytest
from unittest.mock import patch, MagicMock
from PIL import Image


def test_screenshot_returns_dict():
    mock_img = MagicMock(spec=Image.Image)
    mock_img.save = MagicMock()
    fake_bytes = b"fakejpeg"
    import builtins, base64

    with patch("pyautogui.screenshot", return_value=mock_img), \
         patch("backend.engine.windows._desktop_path", return_value="/tmp"), \
         patch("builtins.open", unittest_mock_open(read_data=fake_bytes)):
        from backend.engine.windows import take_screenshot
        result = take_screenshot()

    assert "image_b64" in result
    assert "text" in result
    assert "path" in result


def unittest_mock_open(read_data=b""):
    from unittest.mock import mock_open
    m = mock_open(read_data=read_data)
    return m


def test_sysinfo_cpu():
    from backend.engine.windows import get_system_info
    result = get_system_info("what is my cpu usage")
    assert "%" in result
    assert "CPU" in result or "cpu" in result.lower()


def test_sysinfo_ram():
    from backend.engine.windows import get_system_info
    result = get_system_info("how much ram do I have")
    assert "GB" in result or "MB" in result


def test_sysinfo_disk():
    from backend.engine.windows import get_system_info
    result = get_system_info("how much disk space is left")
    assert "GB" in result or "TB" in result


def test_sysinfo_all():
    from backend.engine.windows import get_system_info
    result = get_system_info("system info")
    assert len(result) > 30


def test_minimize_window_not_found():
    from backend.engine.windows import minimize_window
    with patch("pygetwindow.getAllTitles", return_value=["Notepad", "Chrome"]):
        result = minimize_window("minimize spotify")
    assert result == "Window not found"


def test_minimize_window_found():
    from backend.engine.windows import minimize_window
    mock_win = MagicMock()
    with patch("pygetwindow.getAllTitles", return_value=["Google Chrome", "Notepad"]), \
         patch("pygetwindow.getWindowsWithTitle", return_value=[mock_win]):
        result = minimize_window("minimize chrome")
    mock_win.minimize.assert_called_once()
    assert "Minimized" in result


def test_maximize_window_found():
    from backend.engine.windows import maximize_window
    mock_win = MagicMock()
    with patch("pygetwindow.getAllTitles", return_value=["Notepad - Untitled"]), \
         patch("pygetwindow.getWindowsWithTitle", return_value=[mock_win]):
        result = maximize_window("maximize notepad")
    mock_win.maximize.assert_called_once()
    assert "Maximized" in result


def test_focus_window_found():
    from backend.engine.windows import focus_window
    mock_win = MagicMock()
    with patch("pygetwindow.getAllTitles", return_value=["Spotify"]), \
         patch("pygetwindow.getWindowsWithTitle", return_value=[mock_win]):
        result = focus_window("switch to spotify")
    mock_win.activate.assert_called_once()
    assert "Switched" in result
