import { DEFAULT_SETTINGS } from "../constants";
import type { ChatMessage, ChatSettings } from "../types";

const SETTINGS_KEY = "joketeller.settings.v2";
const MESSAGES_KEY = "joketeller.messages.v2";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

export function loadSettings(): ChatSettings {
  const raw = window.localStorage.getItem(SETTINGS_KEY);
  if (!raw) {
    return { ...DEFAULT_SETTINGS };
  }

  try {
    const parsed = JSON.parse(raw);
    if (!isRecord(parsed)) {
      return { ...DEFAULT_SETTINGS };
    }

    return {
      ...DEFAULT_SETTINGS,
      ...parsed,
    };
  } catch {
    return { ...DEFAULT_SETTINGS };
  }
}

export function saveSettings(settings: ChatSettings): void {
  window.localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
}

export function loadMessages(): ChatMessage[] {
  const raw = window.localStorage.getItem(MESSAGES_KEY);
  if (!raw) {
    return [];
  }

  try {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      return [];
    }

    return parsed.filter(isChatMessage);
  } catch {
    return [];
  }
}

export function saveMessages(messages: ChatMessage[]): void {
  window.localStorage.setItem(MESSAGES_KEY, JSON.stringify(messages));
}

function isChatMessage(value: unknown): value is ChatMessage {
  return (
    isRecord(value) &&
    typeof value.id === "string" &&
    typeof value.role === "string" &&
    typeof value.content === "string" &&
    typeof value.createdAt === "string"
  );
}

