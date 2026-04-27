import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL")  # e.g. https://integrate.api.nvidia.com/v1
    LLM_MODEL: str = os.getenv("LLM_MODEL", "meta/llama3-70b-instruct")
    
    # Image generation (same client or DALL-E compatible endpoint)
    IMAGE_MODEL: str = os.getenv("IMAGE_MODEL", "dall-e-3")
    
    # Web search fallback
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")

    @classmethod
    def validate(cls):
        if not cls.TELEGRAM_TOKEN:
            raise ValueError("TELEGRAM_TOKEN is required in .env")
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required in .env")
