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
