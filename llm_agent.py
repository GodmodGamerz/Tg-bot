import json
import asyncio
from openai import AsyncOpenAI
from config import Config
from tools import web_search

client = AsyncOpenAI(
    api_key=Config.OPENAI_API_KEY,
    base_url=Config.OPENAI_BASE_URL or "https://api.openai.com/v1"
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for real-time information. Use when user asks about current events, facts, or anything beyond your knowledge cutoff.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"]
            }
        }
    }
]

user_histories = {}  # In-memory conversation history (per user)

async def process_prompt(user_id: int, prompt: str) -> str:
    """Tool-calling agent loop. Supports multi-turn via history."""
    if user_id not in user_histories:
        user_histories[user_id] = []
    
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant with real-time web access."}
    ] + user_histories[user_id] + [{"role": "user", "content": prompt}]

    max_iterations = 5
    for _ in range(max_iterations):
        response = await client.chat.completions.create(
            model=Config.LLM_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.7
        )
        msg = response.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        if not msg.tool_calls:
            # Final answer
            user_histories[user_id].append({"role": "user", "content": prompt})
            user_histories[user_id].append({"role": "assistant", "content": msg.content})
            if len(user_histories[user_id]) > 20:  # keep last 10 turns
                user_histories[user_id] = user_histories[user_id][-20:]
            return msg.content or "I have no response."

        # Execute tool(s)
        for tool_call in msg.tool_calls:
            if tool_call.function.name == "web_search":
                args = json.loads(tool_call.function.arguments)
                result = await web_search(args["query"])
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })

    return "I tried my best but couldn't complete the request."
