import { JOKE_STYLE_OPTIONS } from "../constants";
import type { JokeStyle } from "../types";

interface JokeStylePickerProps {
  value: JokeStyle;
  onChange: (value: JokeStyle) => void;
}

export function JokeStylePicker({ value, onChange }: JokeStylePickerProps) {
  return (
    <section className="panel">
      <div className="panel-heading compact">
        <h2>Joke style</h2>
      </div>

      <div className="chip-grid">
        {JOKE_STYLE_OPTIONS.map((option) => (
          <button
            key={option.value}
            type="button"
            className={`chip-button ${value === option.value ? "chip-button-active" : ""}`}
            onClick={() => onChange(option.value)}
          >
            <span>{option.label}</span>
          </button>
        ))}
      </div>
    </section>
  );
}
