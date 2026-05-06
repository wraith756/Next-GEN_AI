from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    assistant_name: str = "jarvis"
    groq_api_key: str = ""
    fast_model: str = "llama-3.1-8b-instant"
    smart_model: str = "llama-3.3-70b-versatile"
    whisper_model: str = "whisper-large-v3"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
