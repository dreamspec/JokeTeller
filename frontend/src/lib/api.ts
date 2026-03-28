import type { ChatRequestPayload, ChatResponse, ErrorPayload, StatusResponse } from "../types";

export class APIClientError extends Error {
  code: string;
  suggestion?: string | null;

  constructor(message: string, code = "frontend_error", suggestion?: string | null) {
    super(message);
    this.name = "APIClientError";
    this.code = code;
    this.suggestion = suggestion;
  }

  get displayMessage(): string {
    return this.suggestion ? `${this.message} ${this.suggestion}` : this.message;
  }
}

export async function getBackendStatus(apiBaseUrl: string): Promise<StatusResponse> {
  try {
    const response = await fetch(buildUrl(apiBaseUrl, "/status"));
    if (!response.ok) {
      throw await parseErrorResponse(response);
    }

    return (await response.json()) as StatusResponse;
  } catch (error) {
    throw normalizeClientError(error, "The frontend could not reach the backend status endpoint.");
  }
}

export async function sendChatRequest(
  apiBaseUrl: string,
  payload: ChatRequestPayload,
): Promise<ChatResponse> {
  try {
    const response = await fetch(buildUrl(apiBaseUrl, "/chat"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw await parseErrorResponse(response);
    }

    return (await response.json()) as ChatResponse;
  } catch (error) {
    throw normalizeClientError(error, "The frontend could not send the chat request.");
  }
}

export async function streamChatRequest(
  apiBaseUrl: string,
  payload: ChatRequestPayload,
  handlers: {
    onChunk: (chunk: string) => void;
    onDone?: (meta: Record<string, unknown>) => void;
  },
): Promise<void> {
  try {
    const response = await fetch(buildUrl(apiBaseUrl, "/chat/stream"), {
      method: "POST",
      headers: {
        Accept: "text/event-stream",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw await parseErrorResponse(response);
    }

    if (!response.body) {
      throw new APIClientError(
        "The backend did not provide a readable streaming response.",
        "stream_missing_body",
      );
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      buffer = await flushBuffer(buffer, handlers);
    }

    if (buffer.trim()) {
      await flushBuffer(`${buffer}\n\n`, handlers);
    }
  } catch (error) {
    throw normalizeClientError(error, "The frontend could not stream the response.");
  }
}

async function flushBuffer(
  buffer: string,
  handlers: {
    onChunk: (chunk: string) => void;
    onDone?: (meta: Record<string, unknown>) => void;
  },
): Promise<string> {
  let workingBuffer = buffer;
  let separatorIndex = workingBuffer.indexOf("\n\n");

  while (separatorIndex !== -1) {
    const rawEvent = workingBuffer.slice(0, separatorIndex).trim();
    workingBuffer = workingBuffer.slice(separatorIndex + 2);

    if (rawEvent) {
      const { event, data } = parseSseEvent(rawEvent);
      if (event === "chunk" && typeof data.content === "string") {
        handlers.onChunk(data.content);
      } else if (event === "error") {
        throw new APIClientError(
          readString(data.message, "Streaming failed."),
          readString(data.code, "stream_error"),
          readOptionalString(data.suggestion),
        );
      } else if (event === "done") {
        handlers.onDone?.(data);
      }
    }

    separatorIndex = workingBuffer.indexOf("\n\n");
  }

  return workingBuffer;
}

function parseSseEvent(rawEvent: string): { event: string; data: Record<string, unknown> } {
  const lines = rawEvent.split(/\r?\n/);
  let event = "message";
  const dataLines: string[] = [];

  for (const line of lines) {
    if (line.startsWith("event:")) {
      event = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trim());
    }
  }

  const parsedData = JSON.parse(dataLines.join(""));
  if (!isRecord(parsedData)) {
    throw new APIClientError("The backend returned an invalid stream payload.", "invalid_stream_payload");
  }

  return { event, data: parsedData };
}

function buildUrl(apiBaseUrl: string, path: string): string {
  return `${apiBaseUrl.replace(/\/$/, "")}${path}`;
}

async function parseErrorResponse(response: Response): Promise<APIClientError> {
  try {
    const payload = (await response.json()) as Partial<ErrorPayload>;
    return new APIClientError(
      readString(payload.message, "The backend request failed."),
      readString(payload.code, "backend_error"),
      readOptionalString(payload.suggestion),
    );
  } catch {
    const fallbackText = await response.text();
    return new APIClientError(fallbackText || "The backend request failed.", "backend_error");
  }
}

function normalizeClientError(error: unknown, fallbackMessage: string): APIClientError {
  if (error instanceof APIClientError) {
    return error;
  }

  if (error instanceof Error) {
    return new APIClientError(fallbackMessage, "network_error", error.message);
  }

  return new APIClientError(fallbackMessage, "network_error");
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function readString(value: unknown, fallback: string): string {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function readOptionalString(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value : undefined;
}

