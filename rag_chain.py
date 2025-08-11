import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from memory_backend import search, upsert_note
from config import config

# Check if API key is valid
if not config.is_valid():
    raise RuntimeError("Invalid configuration. Please check your API keys in .env file.")

chat_model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o")
llm = ChatOpenAI(model=chat_model, temperature=0, api_key=config.OPENAI_API_KEY)

SYS = (
    "You ground answers ONLY in CONTEXT. If insufficient, say you don't know. "
    "After your answer, list any new atomic facts on their own lines as 'FACT: ...'."
)


def answer(query: str, k: int = 5):
    hits = search(query, k)
    ctx = "\n\n".join(doc for _, doc, *_ in hits)

    msgs = [
        SystemMessage(content=SYS),
        HumanMessage(
            content=(
                f"CONTEXT:\n{ctx}\n\n"
                f"QUESTION: {query}\n"
                "Reply first. Then list new facts as 'FACT: ...' on separate lines."
            )
        ),
    ]
    resp = llm.invoke(msgs).content

    blob = " ".join(doc for _, doc, *_ in hits).lower()
    for line in resp.splitlines():
        if line.strip().upper().startswith("FACT:"):
            fact = line[5:].strip()
            if fact and fact.lower() not in blob:
                upsert_note(fact, {"type": "fact", "source": "writeback"})

    used_ids = [h[0] for h in hits]
    return resp, used_ids
