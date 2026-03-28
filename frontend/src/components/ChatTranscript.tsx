import { useEffect, useRef } from "react";

import type { ChatMessage } from "../types";

interface ChatTranscriptProps {
  messages: ChatMessage[];
  isSending: boolean;
}

export function ChatTranscript({ messages, isSending }: ChatTranscriptProps) {
  const transcriptRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    const transcriptElement = transcriptRef.current;
    if (!transcriptElement) {
      return;
    }

    transcriptElement.scrollTop = transcriptElement.scrollHeight;
  }, [messages]);

  if (!messages.length) {
    return (
      <section className="chat-surface surface-card empty-chat">
        <div className="empty-orb">💬</div>
        <h2>Ready when you are</h2>
        <p>Ask for a joke, a gentle code roast, or just a normal answer with a lighter tone.</p>
      </section>
    );
  }

  return (
    <section ref={transcriptRef} className="chat-surface surface-card">
      {messages.map((message) => (
        <article
          key={message.id}
          className={`message-bubble ${message.role === "assistant" ? "message-assistant" : "message-user"}`}
        >
          <div className="message-meta">
            <span>{message.role === "assistant" ? "JokeTeller" : "You"}</span>
            <time>{new Date(message.createdAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</time>
          </div>
          <p>{message.content || (message.role === "assistant" && isSending ? "Thinking..." : "")}</p>
        </article>
      ))}
    </section>
  );
}
