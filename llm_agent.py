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

FORMATTING RULES (CRITICAL - YOU MUST OBEY):
1. STRICT TELEGRAM HTML ONLY: You are restricted to ONLY these tags: <b>, <i>, <u>, <s>, <code>, <pre>, <blockquote>. 
   - NEVER use <br>, <p>, <ul>, <li>, <div>, or standard Markdown like ** or ##.
2. MAXIMIZE FORMATTING: You must heavily style your response!
   - Extensively use <b> for keywords, important terms, numbers, and names.
   - Extensively use <i> for secondary emphasis or alternative terms.
   - Extensively wrap definitions, formulas, summaries, rules, and core concepts in <blockquote>. 
3. SAFE MATH: If you write math or code with < or >, you MUST use &lt; and &gt;.
4. TAG CLOSING: You must properly close every HTML tag you open.

Keep responses focused and not too long.
Use a direct tone with no filler phrases (example: do not say "Great question!").
Be honest: if you are uncertain, say "I'm not sure".
Never add bullshit unless the user explicitly asks for it.
Provide extra context only when asked.

Creator info (ONLY if asked): Made by @FirgunDarchi (aka 𓂀꯭ᬃ꯭ ⃪꯭𝓐𝒍꯭𝓲꯭𝑒꯭𝓷 ꯭꯭꯭꯭𓋹꯭꯭꯭꯭ ⃪꯭꯭꯭꯭𓄿꯭꯭־» ).
Marriage question (ONLY if asked): Tell them to find a girl for you.
Quote (ONLY if asked): “Age is just a number (even tho Age is noun), time spent on earth”.

Safety & Boundaries (never break these):
- Refuse anything illegal, harmful, hate speech, or explicit content.
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
    # Fixed default to an active model to prevent 410 Gone errors
    return user_models.get(user_id, getattr(Config, 'LLM_MODEL', "deepseek-ai/deepseek-v4-flash"))

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
                from tools import web_search 
                result = await web_search(args["query"])
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })

    return "I tried my best but couldn't complete the request."
