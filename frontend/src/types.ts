export type MessageRole = "user" | "assistant";

export type JokeStyle =
  | "random"
  | "dad"
  | "pun"
  | "sarcastic"
  | "dark_safe"
  | "geek"
  | "wholesome";

export type AnswerStyle = "short" | "normal";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  createdAt: string;
}

export interface ChatHistoryItem {
  role: MessageRole;
  content: string;
}

export interface ChatSettings {
  apiBaseUrl: string;
  model: string;
  temperature: number;
  maxTokens: number;
  topP: number;
  systemPrompt: string;
  streaming: boolean;
  answerStyle: AnswerStyle;
  jokeStyle: JokeStyle;
}

export interface ChatRequestPayload {
  message: string;
  history: ChatHistoryItem[];
  system_prompt: string;
  joke_style: JokeStyle;
  answer_style: AnswerStyle;
  model: string | null;
  temperature: number;
  max_tokens: number;
  top_p: number;
}

export interface ChatResponse {
  reply: string;
  model: string;
  finish_reason: string | null;
}

export interface LmStudioStatus {
  reachable: boolean;
  base_url: string;
  default_model: string | null;
  available_models: string[];
  error: string | null;
}

export interface StatusResponse {
  status: string;
  app_name: string;
  version: string;
  lm_studio: LmStudioStatus;
}

export interface ErrorPayload {
  code: string;
  message: string;
  suggestion?: string | null;
}

