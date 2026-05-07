from backend.engine.automation import classify_command


def test_open_command():
    assert classify_command("open chrome") == "open"

def test_close_command():
    assert classify_command("close notepad") == "close"

def test_youtube():
    assert classify_command("play despacito on youtube") == "youtube"

def test_search():
    assert classify_command("search on google python tutorial") == "search"

def test_search_variant():
    assert classify_command("google it what is fastapi") == "search"

def test_message():
    assert classify_command("send message to john") == "message"

def test_status():
    assert classify_command("ai status") == "status"

def test_ai_fallback():
    assert classify_command("what is the meaning of life") == "ai"

def test_open_with_search_word_goes_to_search():
    assert classify_command("open google search") == "search"


def test_classify_screenshot():
    assert classify_command("take a screenshot") == "screenshot"

def test_classify_screenshot_short():
    assert classify_command("screenshot") == "screenshot"

def test_classify_sysinfo_cpu():
    assert classify_command("what is my cpu usage") == "sysinfo"

def test_classify_sysinfo_ram():
    assert classify_command("how much ram do I have") == "sysinfo"

def test_classify_sysinfo_battery():
    assert classify_command("check battery") == "sysinfo"

def test_classify_win_minimize():
    assert classify_command("minimize chrome") == "win_minimize"

def test_classify_win_maximize():
    assert classify_command("maximize notepad") == "win_maximize"

def test_classify_win_focus():
    assert classify_command("focus spotify") == "win_focus"

def test_classify_switch_to():
    assert classify_command("switch to chrome") == "win_focus"
