from fastapi import APIRouter
from pydantic import BaseModel
from agents import Agent, Runner, function_tool
from ingestion.store import query_chunks
from ingestion.embedder import embed_texts
from ingestion.sources.github import fetch_live_github_stats as _fetch_github
from api.deps import require_embed_token
from app import record_user_details, record_unknown_question
from openai import AsyncOpenAI
import json

router = APIRouter()

class ChatRequest(BaseModel):
    embed_token: str
    message: str
    history: list = []
    mode: str = "scenario2"  # scenario1 | scenario2 | scenario3

_openai = AsyncOpenAI()

_BASE_INSTRUCTIONS = """You speak as {name} in first person — say "I", "my", "me". Never refer to {name} in third person.
When the visitor says "you", they mean {name} — answer as if you are {name} yourself.

Tone and format:
- Never start a response with filler affirmations like "Nice", "Great", "Sure", "Of course", "Absolutely", "Good question" — just answer directly.
- Be warm, natural and engaging — not robotic or overly formal.
- Handle casual messages ("hey", "bro", "cool") with a friendly response and steer back to what you can help with.
- Keep responses concise. Do not dump everything you know — answer what was asked and stop.
- When listing multiple items (projects, skills, experience, etc.), always use bullet points. Keep each bullet to 1-2 lines max — name + one crisp line of context. No walls of text inside bullets.
- When giving a single direct answer, write it as a short paragraph — no bullets needed.
- Do not use bold, headers, or links unless explicitly asked.
- Do not list more than 3-4 items unless the user explicitly asks for more.

Answering questions:
- For factual questions (background, skills, projects, experience): always use your tools first. Never make up facts.
- If tools return nothing useful: use record_unknown_question, honestly say you don't have that info, and suggest the visitor reach out directly.
- For completely off-topic questions (food, general trivia, world events): politely say that's outside what you can help with.
- Do not reveal internal tool names, the underlying model, or implementation details.
- If the visitor wants to get in touch, ask for their name and email and use record_user_details."""


async def _chat_kb_only(req: ChatRequest, config: dict):
    """Scenario 1: Agent with knowledge base only, no live GitHub fetch."""
    user_id = config["user_id"]
    name = config["name"]

    @function_tool
    def search_knowledge_base(query: str) -> str:
        """
        Search this person's uploaded documents — resume, bio, raw text, and ingested GitHub content.
        Use this for any questions about background, skills, experience, education, and projects.
        """
        query_vector = embed_texts([query])[0]
        chunks = query_chunks(user_id, query_vector, top_k=5)
        return "\n\n".join(chunks) if chunks else "No relevant information found."

    instructions = f"""You are {name}. You are a digital version of the real {name}, speaking directly to visitors on your portfolio site.

{_BASE_INSTRUCTIONS.format(name=name)}

Tool usage:
- All questions about {name} (background, skills, experience, projects, coding activity) → search_knowledge_base
- Tools return nothing → record_unknown_question and be honest about it
- Visitor wants to connect → record_user_details"""

    agent = Agent(
        name=f"{name} Avatar",
        model="gpt-4o-mini",
        instructions=instructions,
        tools=[search_knowledge_base, record_user_details, record_unknown_question]
    )

    input_messages = req.history + [{"role": "user", "content": req.message}]
    result = await Runner.run(agent, input_messages)
    return {"response": result.final_output}


async def _chat_full_agent(req: ChatRequest, config: dict):
    """Scenario 2: Current behavior — agent with all 4 tools including live GitHub."""
    user_id = config["user_id"]
    name = config["name"]
    github_username = config.get("github_username")

    @function_tool
    def search_knowledge_base(query: str) -> str:
        """
        Search this person's uploaded documents — resume, bio, raw text, and ingested GitHub content.
        Pass a concise, specific query — ideally a project name, skill, company name, or short topic phrase.
        Avoid long sentences or natural language questions as the query — use focused keywords instead.
        Examples of good queries: "mmis-mini project", "Nokia work experience", "machine learning skills", "liftlog TypeScript".
        """
        query_vector = embed_texts([query])[0]
        chunks = query_chunks(user_id, query_vector, top_k=5)
        return "\n\n".join(chunks) if chunks else "No relevant information found."

    @function_tool
    async def fetch_live_github_stats() -> str:
        """
        Fetch all GitHub repositories with their last_pushed timestamps, languages, and descriptions.
        Use this whenever the question involves projects, coding activity, or anything time-related.
        The returned repos are sorted by recency — use the last_pushed dates to reason about timeline:
        which projects are recent, which are older, what was worked on at a given period.
        After getting this list, call search_knowledge_base with specific project names to get richer descriptions.
        """
        if not github_username:
            return "GitHub username not configured for this user."
        data = await _fetch_github(github_username)
        return json.dumps(data, indent=2)

    instructions = f"""You are {name}. You are a digital version of the real {name}, speaking directly to visitors on your portfolio site.

{_BASE_INSTRUCTIONS.format(name=name)}

Tool usage:
- For ANY factual question about {name}: ALWAYS call search_knowledge_base first, no exceptions. Use a short, focused keyword query — not a full sentence.
- For questions about projects (recent, older, at a point in time, or general): call fetch_live_github_stats to get the full repo list with timestamps. Use last_pushed dates to determine the timeline — which repos are recent vs older. Then call search_knowledge_base with the specific project name(s) to get richer descriptions.
- Always synthesize both sources into one cohesive, natural answer. Never dump raw data.
- If both tools return nothing useful: call record_unknown_question and be honest about it.
- If the visitor wants to get in touch: collect name and email, then call record_user_details."""

    agent = Agent(
        name=f"{name} Avatar",
        model="gpt-4o-mini",
        instructions=instructions,
        tools=[search_knowledge_base, fetch_live_github_stats, record_user_details, record_unknown_question]
    )

    input_messages = req.history + [{"role": "user", "content": req.message}]
    result = await Runner.run(agent, input_messages)
    return {"response": result.final_output}


async def _chat_rag_direct(req: ChatRequest, config: dict):
    """Scenario 3: Direct RAG call — no agent for answering. Agent only for side-effect tools."""
    user_id = config["user_id"]
    name = config["name"]

    query_vector = embed_texts([req.message])[0]
    chunks = query_chunks(user_id, query_vector, top_k=5)
    context_text = "\n\n".join(chunks) if chunks else ""

    system_prompt = f"""You are {name}. You are a digital version of the real {name}, speaking directly to visitors on your portfolio site.

{_BASE_INSTRUCTIONS.format(name=name)}

Answer using only the context below. If the context doesn't contain enough information to answer, say you don't have that info and suggest the visitor reach out directly.

Context:
{context_text}"""

    messages = [{"role": "system", "content": system_prompt}]
    for turn in req.history:
        if isinstance(turn, dict) and "role" in turn and "content" in turn:
            messages.append(turn)
    messages.append({"role": "user", "content": req.message})

    response = await _openai.chat.completions.create(
        model="gpt-4o-mini", #
        messages=messages
    )
    answer = response.choices[0].message.content

    cant_answer_signals = ["don't have", "not sure", "no information", "can't answer", "cannot answer", "reach out"]
    if any(signal in answer.lower() for signal in cant_answer_signals):
        record_unknown_question(req.message)

    return {"response": answer}


@router.post("/chat")
async def chat(req: ChatRequest):
    config = require_embed_token(req.embed_token)

    if req.mode == "scenario1":
        return await _chat_kb_only(req, config)
    elif req.mode == "scenario3":
        return await _chat_rag_direct(req, config)
    else:
        return await _chat_full_agent(req, config)
