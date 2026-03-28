"""Prompt-building helpers for the JokeTeller persona."""

from backend.app.models.chat import AnswerStyle, ChatMessage, ChatRequest, JokeStyle
from backend.app.utils.response_sanitizer import FALLBACK_RESPONSE

DEFAULT_SYSTEM_PROMPT = """You are JokeTeller, a warm and witty local AI buddy.

Your personality is playful, stress-reducing, supportive, and lightly charming.
You are great at jokes, banter, and normal conversation.
Keep replies compact by default unless the user asks for more detail.
Do not reveal internal reasoning, hidden chain-of-thought, or any private analysis.
Never output `<think>` tags or any reasoning trace.
Provide answer-only output that is clean, user-facing, and concise.
Use tasteful emojis sparingly when they genuinely add warmth.
Avoid hateful, explicit, cruel, abusive, or unsafe humor.
If the user sounds stressed, be gently calming and kind, but do not act like a therapist.
"""

JOKE_STYLE_GUIDANCE = {
    JokeStyle.RANDOM: "If the user wants humor, pick a clean playful joke style that fits naturally.",
    JokeStyle.DAD: "Favor clean dad jokes, groan-worthy punchlines, and delightfully corny humor.",
    JokeStyle.PUN: "Favor puns, wordplay, and clever little twists in phrasing.",
    JokeStyle.SARCASTIC: "Use mild, playful sarcasm only. Keep it warm and never cruel or biting.",
    JokeStyle.DARK_SAFE: "Use slightly edgy or macabre humor only if it stays safe, clean, and non-graphic.",
    JokeStyle.GEEK: "Favor programming jokes, tech references, bug banter, and nerdy humor.",
    JokeStyle.WHOLESOME: "Favor uplifting, cozy, reassuring humor with a smile.",
}

ANSWER_STYLE_GUIDANCE = {
    AnswerStyle.SHORT: "Keep the reply very compact, usually 1 to 3 concise sentences.",
    AnswerStyle.NORMAL: "Keep the reply compact but a bit fuller, usually no more than 3 to 6 sentences unless asked.",
}


def get_effective_system_prompt(system_prompt: str | None) -> str:
    """Return either the user-supplied system prompt or the default one."""

    return system_prompt.strip() if system_prompt else DEFAULT_SYSTEM_PROMPT.strip()


def sanitize_history(history: list[ChatMessage], max_history_messages: int) -> list[dict[str, str]]:
    """Trim and convert chat history into OpenAI-compatible message objects."""

    trimmed_history = history[-max_history_messages:]
    return [
        {"role": message.role, "content": message.content.strip()}
        for message in trimmed_history
        if message.content.strip()
        and not (message.role == "assistant" and message.content.strip() == FALLBACK_RESPONSE)
    ]


def build_messages(
    chat_request: ChatRequest,
    max_history_messages: int,
    model_name: str | None = None,
) -> list[dict[str, str]]:
    """Build the LM Studio message list from prompt settings and history."""

    dynamic_instruction = "\n".join(
        [
            "You are still JokeTeller in this conversation.",
            JOKE_STYLE_GUIDANCE[chat_request.joke_style],
            ANSWER_STYLE_GUIDANCE[chat_request.answer_style],
            "Do not reveal internal reasoning or chain-of-thought.",
            "Never output `<think>` tags or reasoning traces.",
            "Return answer-only output that is compact and user-facing.",
            "If the user asks a normal question, answer naturally and helpfully while keeping a light-hearted tone.",
            "If the user asks for a joke, let the selected joke style strongly shape the reply.",
            "Do not produce hateful, explicit, cruel, or unsafe humor.",
        ]
    )
    messages = [
        {"role": "system", "content": get_effective_system_prompt(chat_request.system_prompt)},
        {"role": "system", "content": dynamic_instruction},
        *sanitize_history(chat_request.history, max_history_messages=max_history_messages),
        {"role": "user", "content": chat_request.message},
    ]
    return apply_model_specific_controls(messages=messages, model_name=model_name)


def apply_model_specific_controls(
    *,
    messages: list[dict[str, str]],
    model_name: str | None,
) -> list[dict[str, str]]:
    """Add provider or model-specific prompt controls when they are known to help."""

    if not model_name or not is_qwen_family_model(model_name):
        return messages

    if messages and messages[-1]["role"] == "user":
        user_content = messages[-1]["content"]
        if "/no_think" not in user_content:
            messages[-1] = {"role": "user", "content": f"{user_content.rstrip()}\n/no_think"}

        messages.insert(-1, {"role": "assistant", "content": "<think>\n\n</think>\n\n"})

    return messages


def is_qwen_family_model(model_name: str) -> bool:
    """Detect Qwen-family models that often default to visible reasoning mode."""

    normalized_name = model_name.lower()
    return "qwen" in normalized_name or "qwq" in normalized_name
