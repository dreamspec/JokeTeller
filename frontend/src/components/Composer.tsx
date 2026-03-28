import type { KeyboardEvent } from "react";

interface ComposerProps {
  value: string;
  disabled: boolean;
  onChange: (value: string) => void;
  onSubmit: () => void;
}

export function Composer({ value, disabled, onChange, onSubmit }: ComposerProps) {
  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      onSubmit();
    }
  };

  return (
    <section className="composer surface-card">
      <div className="composer-topline">
        <strong>Say something</strong>
        <span>Enter to send</span>
      </div>
      <textarea
        className="composer-input"
        placeholder="Ask for a joke, vent about a bug, or invite a tiny bit of banter..."
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        rows={4}
      />
      <div className="composer-actions">
        <span className="composer-hint">Runs locally through FastAPI and LM Studio.</span>
        <button className="primary-button" type="button" onClick={onSubmit} disabled={disabled || !value.trim()}>
          {disabled ? "Working..." : "Send message"}
        </button>
      </div>
    </section>
  );
}
