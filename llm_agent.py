import json
import asyncio
from openai import AsyncOpenAI
from config import Config

client = AsyncOpenAI(
    api_key=Config.OPENAI_API_KEY,
    base_url=Config.OPENAI_BASE_URL
)

# Per-user model selection (in-memory, resets on bot restart - good enough for now)
user_models = {}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for real-time information.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"]
            }
        }
    }
]

user_histories = {}

def get_user_model(user_id: int) -> str:
    """Get user's selected model or fall back to default"""
    return user_models.get(user_id, Config.DEFAULT_MODEL)

def set_user_model(user_id: int, model: str):
    """Save user's chosen model"""
    user_models[user_id] = model

async def process_prompt(user_id: int, prompt: str) -> str:
    model = get_user_model(user_id)
    
    if user_id not in user_histories:
        user_histories[user_id] = []
    
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant with real-time web access."}
    ] + user_histories[user_id] + [{"role": "user", "content": prompt}]

    max_iterations = 5
    for _ in range(max_iterations):
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.7
        )
        msg = response.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        if not msg.tool_calls:
            user_histories[user_id].append({"role": "user", "content": prompt})
            user_histories[user_id].append({"role": "assistant", "content": msg.content})
            if len(user_histories[user_id]) > 20:
                user_histories[user_id] = user_histories[user_id][-20:]
            return msg.content or "I have no response."

        for tool_call in msg.tool_calls:
            if tool_call.function.name == "web_search":
                args = json.loads(tool_call.function.arguments)
                from tools import web_search
                result = await web_search(args["query"])
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })

    return "I tried my best but couldn't complete the request."
