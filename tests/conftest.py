# tests/conftest.py

# Standard Libraries
import os


# Test environment
os.environ.setdefault("PYTHON_DOTENV_DISABLED", "1")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("COINGECKO_API_KEY", "test-api-key")
