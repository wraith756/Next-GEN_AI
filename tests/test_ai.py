from unittest.mock import MagicMock, patch
from backend.engine.ai import route_model, compress_history


def test_route_short_query_uses_fast_model():
    assert route_model("open chrome") == "llama-3.1-8b-instant"


def test_route_complex_query_uses_smart_model():
    result = route_model("why is machine learning so powerful and how does it work")
    assert result == "llama-3.3-70b-versatile"


def test_route_9_words_no_question_uses_fast():
    result = route_model("play some music on youtube please now today here")
    assert result == "llama-3.1-8b-instant"


def test_route_8_words_with_question_word_uses_fast():
    result = route_model("how are you doing today")
    assert result == "llama-3.1-8b-instant"


def test_compress_history_calls_groq():
    messages = [
        {"role": "user", "content": "What is Python?"},
        {"role": "assistant", "content": "Python is a programming language."},
    ] * 5
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value.choices[0].message.content = "User asked about Python."
    with patch("backend.engine.ai._client", mock_client):
        result = compress_history(messages)
    assert result == "User asked about Python."
    mock_client.chat.completions.create.assert_called_once()
