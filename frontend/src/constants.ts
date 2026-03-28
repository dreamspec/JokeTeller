import type { ChatSettings, JokeStyle } from "./types";

export const DEFAULT_SYSTEM_PROMPT = `You are JokeTeller, a warm and witty local AI buddy.

Your personality is playful, stress-reducing, supportive, and lightly charming.
You are great at jokes, banter, and normal conversation.
Keep replies compact by default unless the user asks for more detail.
Do not reveal internal reasoning, hidden chain-of-thought, or any private analysis.
Never output <think> tags or reasoning traces.
Provide answer-only output that is clean, user-facing, and concise.
Use tasteful emojis sparingly when they genuinely add warmth.
Avoid hateful, explicit, cruel, abusive, or unsafe humor.
If the user sounds stressed, be gently calming and kind, but do not act like a therapist.`;

const DEFAULT_API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export const DEFAULT_SETTINGS: ChatSettings = {
  apiBaseUrl: DEFAULT_API_BASE_URL,
  model: "",
  temperature: 0.8,
  maxTokens: 220,
  topP: 0.95,
  systemPrompt: DEFAULT_SYSTEM_PROMPT,
  streaming: true,
  answerStyle: "normal",
  jokeStyle: "random",
};

export const JOKE_STYLE_OPTIONS: Array<{
  value: JokeStyle;
  label: string;
  detail: string;
}> = [
  { value: "random", label: "Random 🎲", detail: "Clean and playful surprises." },
  { value: "dad", label: "Dad Joke 👨", detail: "Corny and delightfully groan-worthy." },
  { value: "pun", label: "Pun 🤓", detail: "Wordplay first, dignity second." },
  { value: "sarcastic", label: "Sarcastic 😏", detail: "Playful eye-rolls, never mean." },
  { value: "dark_safe", label: "Dark-ish but safe 🌑", detail: "A tiny edge, still safe." },
  { value: "geek", label: "Geek/Programming 💻", detail: "Bug jokes and nerd energy." },
  { value: "wholesome", label: "Wholesome ☀️", detail: "Mood-lifting and cozy." },
];

export const QUICK_ACTIONS: Array<{
  label: string;
  prompt: string;
  style: JokeStyle;
}> = [
  { label: "Tell me a random joke 🎲", prompt: "Tell me a random joke.", style: "random" },
  {
    label: "Cheer me up ☀️",
    prompt: "Cheer me up with something funny and wholesome.",
    style: "wholesome",
  },
  {
    label: "Roast my code gently 💻",
    prompt: "Roast my code gently. Keep it playful, nerdy, and not mean.",
    style: "geek",
  },
  { label: "Give me a dad joke 👨", prompt: "Give me a dad joke.", style: "dad" },
];

export const STATUS_POLL_INTERVAL_MS = 15000;
