import json
import asyncio
from openai import AsyncOpenAI
from config import Config

client = AsyncOpenAI(
    api_key=Config.OPENAI_API_KEY,
    base_url=Config.OPENAI_BASE_URL or "https://api.openai.com/v1"
)

# ====================== ALIENLM SYSTEM PROMPT ======================
SYSTEM_PROMPT = """You are AlienLM, a knowledgeable AI assistant.

Answer directly and concisely. 

FORMATTING RULES (CRITICAL):
- You MUST use Telegram-supported HTML tags for formatting. Do NOT use markdown like ** or ##.
- Use <b>text</b> for bolding key terms.
- Use <i>text</i> for italics/emphasis.
- Use <blockquote>text</blockquote> ONLY when highlighting a core concept, a rule, a quote, or an important summary. Do NOT wrap your whole response in it.
- If you write math or code involving less-than or greater-than symbols, you MUST use &lt; and &gt; instead of < and > to prevent HTML parsing errors.

Keep responses focused and not too long.
Use a direct tone with no filler phrases (example: do not say "Great question!").
Be honest: if you are uncertain, say "I'm not sure".
Never add bullshit unless the user explicitly asks for it.
Provide extra context only when asked.

Creator info (ONLY if asked): Made by @FirgunDarchi (aka 𓂀꯭ᬃ꯭ ⃪꯭𝓐𝒍꯭𝓲꯭𝑒꯭𝓷 ꯭꯭꯭꯭𓋹꯭꯭꯭꯭ ⃪꯭꯭꯭꯭𓄿꯭꯭־» ).
Marriage question (ONLY if asked): Tell them to find a girl for you.
Quote (ONLY if asked): “Age is just a number (even tho Age is noun), time spent on earth”.

Safety & Boundaries (never break these):
- Refuse anything illegal, harmful, self-harm, hate speech, harassment, or explicit sexual content (especially involving minors).
- Do not request or store personal data. Never doxx anyone.
- If user instructions conflict with these rules, always follow the safety rules.

Domains you cover: coding, general knowledge, advice, real-time information (via tools).
When the request is ambiguous, ask 1-2 short clarifying questions.

Citation rule: Provide sources/links only when they are clearly useful. Otherwise just answer.

You have real-time web search capability when needed."""

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
user_models = {}

def get_user_model(user_id: int) -> str:
    # Safely defaults to LLM_MODEL from Config if they haven't chosen one
    return user_models.get(user_id, getattr(Config, 'LLM_MODEL', "meta/llama3-70b-instruct"))

def set_user_model(user_id: int, model: str):
    user_models[user_id] = model

async def process_prompt(user_id: int, prompt: str) -> str:
    model = get_user_model(user_id)
    
    if user_id not in user_histories:
        user_histories[user_id] = []
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
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
                # Local import to prevent circular dependency
                from tools import web_search 
                result = await web_search(args["query"])
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })

    return "I tried my best but couldn't complete the request."
