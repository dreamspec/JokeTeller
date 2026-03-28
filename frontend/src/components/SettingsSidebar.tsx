import type { ChangeEvent } from "react";

import { DEFAULT_SETTINGS } from "../constants";
import type { ChatSettings } from "../types";

interface SettingsSidebarProps {
  settings: ChatSettings;
  availableModels: string[];
  onChange: (patch: Partial<ChatSettings>) => void;
  onReset: () => void;
  onClearChat: () => void;
}

export function SettingsSidebar({
  settings,
  availableModels,
  onChange,
  onReset,
  onClearChat,
}: SettingsSidebarProps) {
  const handleApiBaseUrl = (event: ChangeEvent<HTMLInputElement>) => {
    onChange({ apiBaseUrl: event.target.value });
  };

  const handleModel = (event: ChangeEvent<HTMLInputElement>) => {
    onChange({ model: event.target.value });
  };

  const handleSystemPrompt = (event: ChangeEvent<HTMLTextAreaElement>) => {
    onChange({ systemPrompt: event.target.value });
  };

  const handleTemperature = (event: ChangeEvent<HTMLInputElement>) => {
    onChange({ temperature: Number(event.target.value) });
  };

  const handleMaxTokens = (event: ChangeEvent<HTMLInputElement>) => {
    onChange({ maxTokens: Number(event.target.value) });
  };

  const handleTopP = (event: ChangeEvent<HTMLInputElement>) => {
    onChange({ topP: Number(event.target.value) });
  };

  return (
    <aside className="settings-rail surface-card">
      <div className="settings-header">
        <span className="settings-eyebrow">Left pane</span>
        <h2>Tuning Booth</h2>
        <p>Shape the vibe without touching the backend contract.</p>
      </div>

      <label className="field">
        <span>Backend URL</span>
        <input type="text" value={settings.apiBaseUrl} onChange={handleApiBaseUrl} />
      </label>

      <label className="field">
        <span>Model name</span>
        <input
          type="text"
          value={settings.model}
          onChange={handleModel}
          list="available-models"
          placeholder="Leave blank to auto-pick"
        />
        <datalist id="available-models">
          {availableModels.map((model) => (
            <option key={model} value={model} />
          ))}
        </datalist>
      </label>

      <label className="field">
        <div className="field-row">
          <span>Temperature</span>
          <strong>{settings.temperature.toFixed(2)}</strong>
        </div>
        <input
          type="range"
          min={0}
          max={2}
          step={0.05}
          value={settings.temperature}
          onChange={handleTemperature}
        />
      </label>

      <label className="field">
        <div className="field-row">
          <span>Max tokens</span>
          <strong>{settings.maxTokens}</strong>
        </div>
        <input
          type="range"
          min={32}
          max={1024}
          step={16}
          value={settings.maxTokens}
          onChange={handleMaxTokens}
        />
      </label>

      <label className="field">
        <div className="field-row">
          <span>Top p</span>
          <strong>{settings.topP.toFixed(2)}</strong>
        </div>
        <input
          type="range"
          min={0.1}
          max={1}
          step={0.05}
          value={settings.topP}
          onChange={handleTopP}
        />
      </label>

      <div className="field">
        <span>Answer style</span>
        <div className="segmented-control">
          {(["short", "normal"] as const).map((option) => (
            <button
              key={option}
              type="button"
              className={`segment ${settings.answerStyle === option ? "segment-active" : ""}`}
              onClick={() => onChange({ answerStyle: option })}
            >
              {option === "short" ? "Short" : "Normal"}
            </button>
          ))}
        </div>
      </div>

      <label className="toggle-row">
        <div>
          <strong>Streaming</strong>
          <span>Progressive token rendering from `/chat/stream`.</span>
        </div>
        <input
          type="checkbox"
          checked={settings.streaming}
          onChange={(event) => onChange({ streaming: event.target.checked })}
        />
      </label>

      <label className="field">
        <span>System prompt</span>
        <textarea value={settings.systemPrompt} onChange={handleSystemPrompt} rows={10} />
      </label>

      <div className="sidebar-actions">
        <button className="secondary-button" type="button" onClick={onReset}>
          Reset settings
        </button>
        <button className="ghost-button" type="button" onClick={onClearChat}>
          Clear chat
        </button>
      </div>

      <div className="settings-footer">
        <p>Default model fallback stays on the backend.</p>
        <p>Default temperature: {DEFAULT_SETTINGS.temperature.toFixed(2)}</p>
      </div>
    </aside>
  );
}
