import os
from pathlib import Path


def load_env_file():
    """
    Load environment variables from .env file
    """
    env_path = Path(__file__).resolve().parent.parent / ".env"

    if not env_path.exists():
        print(".env file not found")
        return

    with open(env_path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            # Ignore comments and empty lines
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)

            key = key.strip()
            value = value.strip().strip('"').strip("'")

            # Load only if not already present
            if key and key not in os.environ:
                os.environ[key] = value


# Load .env
load_env_file()

# Assistant Settings
ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "jarvis")

# Provider:
# auto / gemini / xai
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto").lower()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
XAI_API_KEY = os.getenv("XAI_API_KEY", "") or os.getenv("GROK_API_KEY", "")

# Model Names
GROK_MODEL = os.getenv("GROK_MODEL", "grok-2-latest")

# Final Key Selection
if LLM_PROVIDER == "gemini":
    LLM_KEY = GEMINI_API_KEY

elif LLM_PROVIDER in ("xai", "grok"):
    LLM_KEY = XAI_API_KEY

else:
    # AUTO MODE
    LLM_KEY = XAI_API_KEY or GEMINI_API_KEY