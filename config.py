import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://integrate.api.nvidia.com/v1")
    
    # Default model (you can change this anytime)
    DEFAULT_MODEL: str = "nvidia/nemotron-3-super-120b-a12b"
    
    # Available models for the /model command
    AVAILABLE_MODELS = {
        "Nemotron": "nvidia/nemotron-3-super-120b-a12b",
        "GPT": "openai/gpt-oss-120b",
        "DeepSeek": "deepseek-ai/deepseek-v4-pro"
    }

    @classmethod
    def validate(cls):
        if not cls.TELEGRAM_TOKEN:
            raise ValueError("TELEGRAM_TOKEN is required")
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required")
