import json
from dataclasses import dataclass

from groq import Groq


SYSTEM_PROMPT = """You evaluate prediction markets for a news digest. Respond in JSON only.
A market is newsworthy if: (1) it concerns events affecting many people, and (2) the current odds reveal something the mainstream news isn't stating clearly.
Reject: celebrity gossip, social media metrics, crypto price bets, trivial predictions."""


@dataclass
class LLMResult:
    worthy: bool
    summary: str | None


def judge_market(
    question: str,
    category: str,
    probability: float,
    change: float,
    api_key: str,
) -> LLMResult:
    """Use Groq LLM to judge if a market is newsworthy and generate a summary."""
    client = Groq(api_key=api_key)

    change_str = f"+{change*100:.0f}%" if change >= 0 else f"{change*100:.0f}%"
    user_prompt = f"""Market: {question}
Category: {category}
Current: {probability*100:.0f}% | 24h change: {change_str}

{{"worthy": true/false, "summary": "2-3 sentences if worthy, else null"}}"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=200,
    )

    content = response.choices[0].message.content
    try:
        data = json.loads(content)
        return LLMResult(
            worthy=data.get("worthy", False),
            summary=data.get("summary"),
        )
    except (json.JSONDecodeError, KeyError):
        return LLMResult(worthy=False, summary=None)
