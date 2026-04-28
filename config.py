import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://integrate.api.nvidia.com/v1")
    
    # The default model is now the active DeepSeek Flash to prevent 410 errors
    LLM_MODEL: str = os.getenv("LLM_MODEL", "deepseek-ai/deepseek-v4-flash") 
    
    IMAGE_MODEL: str = os.getenv("IMAGE_MODEL", "dall-e-3") 
    
    # 🛠️ THE FIX: This line prevents the "Config has no attribute TAVILY_API_KEY" error
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")

    # Used by handlers.py to display nice names in the inline keyboard
    AVAILABLE_MODELS = {
        "nvidia/nemotron-3-super-120b-a12b": "🟢 Nemotron",
        "openai/gpt-oss-120b": "🔵 GPT",
        "deepseek-ai/deepseek-v4-pro": "🔴 DeepSeek Pro",
        "deepseek-ai/deepseek-v4-flash": "⚡ DeepSeek Flash"
    }

    @classmethod
    def validate(cls):
        if not cls.TELEGRAM_TOKEN:
            raise ValueError("TELEGRAM_TOKEN is required in .env or Railway Variables")
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required in .env or Railway Variables")
