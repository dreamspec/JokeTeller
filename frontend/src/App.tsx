import { useEffect, useState } from "react";

import { DEFAULT_SETTINGS, STATUS_POLL_INTERVAL_MS } from "./constants";
import { Composer } from "./components/Composer";
import { ChatTranscript } from "./components/ChatTranscript";
import { Header } from "./components/Header";
import { JokeStylePicker } from "./components/JokeStylePicker";
import { QuickActions } from "./components/QuickActions";
import { SettingsSidebar } from "./components/SettingsSidebar";
import { StatusPanel } from "./components/StatusPanel";
import { APIClientError, getBackendStatus, sendChatRequest, streamChatRequest } from "./lib/api";
import { loadMessages, loadSettings, saveMessages, saveSettings } from "./lib/storage";
import type { ChatHistoryItem, ChatMessage, ChatRequestPayload, ChatSettings, JokeStyle, StatusResponse } from "./types";

function App() {
  const [settings, setSettings] = useState<ChatSettings>(() => loadSettings());
  const [messages, setMessages] = useState<ChatMessage[]>(() => loadMessages());
  const [draft, setDraft] = useState("");
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [statusLoading, setStatusLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);

  useEffect(() => {
    saveSettings(settings);
  }, [settings]);

  useEffect(() => {
    saveMessages(messages);
  }, [messages]);

  useEffect(() => {
    let cancelled = false;

    const refreshStatus = async () => {
      if (!cancelled) {
        setStatusLoading(true);
      }

      try {
        const nextStatus = await getBackendStatus(settings.apiBaseUrl);
        if (cancelled) {
          return;
        }
        setStatus(nextStatus);
        setStatusError(null);
      } catch (error) {
        if (cancelled) {
          return;
        }
        const clientError =
          error instanceof APIClientError
            ? error
            : new APIClientError("Unable to refresh backend status.");
        setStatus(null);
        setStatusError(clientError.displayMessage);
      } finally {
        if (!cancelled) {
          setStatusLoading(false);
        }
      }
    };

    void refreshStatus();
    const intervalId = window.setInterval(() => {
      void refreshStatus();
    }, STATUS_POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [settings.apiBaseUrl]);

  const availableModels = status?.lm_studio.available_models ?? [];

  const updateSettings = (patch: Partial<ChatSettings>) => {
    setSettings((current) => ({ ...current, ...patch }));
  };

  const resetSettings = () => {
    setSettings({ ...DEFAULT_SETTINGS });
  };

  const clearChat = () => {
    setMessages([]);
  };

  const refreshStatusNow = async () => {
    setStatusLoading(true);
    try {
      const nextStatus = await getBackendStatus(settings.apiBaseUrl);
      setStatus(nextStatus);
      setStatusError(null);
    } catch (error) {
      const clientError =
        error instanceof APIClientError ? error : new APIClientError("Unable to refresh backend status.");
      setStatus(null);
      setStatusError(clientError.displayMessage);
    } finally {
      setStatusLoading(false);
    }
  };

  const submitMessage = async (rawMessage: string, jokeStyleOverride?: JokeStyle) => {
    const message = rawMessage.trim();
    if (!message || isSending) {
      return;
    }

    const history = toHistory(messages);
    const userMessage = createMessage("user", message);
    const assistantMessage = createMessage("assistant", "");

    setDraft("");
    setIsSending(true);
    setMessages((current) => [...current, userMessage, assistantMessage]);

    const payload: ChatRequestPayload = {
      message,
      history,
      system_prompt: settings.systemPrompt,
      joke_style: jokeStyleOverride ?? settings.jokeStyle,
      answer_style: settings.answerStyle,
      model: settings.model.trim() || null,
      temperature: settings.temperature,
      max_tokens: settings.maxTokens,
      top_p: settings.topP,
    };

    try {
      if (settings.streaming) {
        let streamedContent = "";
        let finalStreamedReply = "";
        await streamChatRequest(settings.apiBaseUrl, payload, {
          onChunk: (chunk) => {
            streamedContent += chunk;
            setMessages((current) =>
              current.map((item) =>
                item.id === assistantMessage.id ? { ...item, content: streamedContent } : item,
              ),
            );
          },
          onDone: (meta) => {
            const finalReply = typeof meta.reply === "string" ? meta.reply : streamedContent;
            finalStreamedReply = finalReply;
            setMessages((current) =>
              current.map((item) =>
                item.id === assistantMessage.id ? { ...item, content: finalReply } : item,
              ),
            );
          },
        });

        if (!(finalStreamedReply || streamedContent).trim()) {
          throw new APIClientError("The model returned an empty response.");
        }
      } else {
        const response = await sendChatRequest(settings.apiBaseUrl, payload);
        setMessages((current) =>
          current.map((item) =>
            item.id === assistantMessage.id ? { ...item, content: response.reply } : item,
          ),
        );
      }
    } catch (error) {
      const clientError =
        error instanceof APIClientError ? error : new APIClientError("The conversation request failed.");
      setMessages((current) =>
        current.map((item) =>
          item.id === assistantMessage.id ? { ...item, content: clientError.displayMessage } : item,
        ),
      );
    } finally {
      setIsSending(false);
      void refreshStatusNow();
    }
  };

  return (
    <div className="app-shell">
      <SettingsSidebar
        settings={settings}
        availableModels={availableModels}
        onChange={updateSettings}
        onReset={resetSettings}
        onClearChat={clearChat}
      />

      <main className="main-column">
        <Header />
        <StatusPanel
          status={status}
          statusError={statusError}
          loading={statusLoading}
          onRefresh={refreshStatusNow}
        />
        <JokeStylePicker value={settings.jokeStyle} onChange={(value) => updateSettings({ jokeStyle: value })} />
        <QuickActions disabled={isSending} onRun={submitMessage} />
        <ChatTranscript messages={messages} isSending={isSending} />
        <Composer value={draft} onChange={setDraft} onSubmit={() => void submitMessage(draft)} disabled={isSending} />
      </main>
    </div>
  );
}

function createMessage(role: ChatMessage["role"], content: string): ChatMessage {
  return {
    id: `${role}-${crypto.randomUUID()}`,
    role,
    content,
    createdAt: new Date().toISOString(),
  };
}

function toHistory(messages: ChatMessage[]): ChatHistoryItem[] {
  return messages.map(({ role, content }) => ({ role, content }));
}

export default App;
