import { QUICK_ACTIONS } from "../constants";
import type { JokeStyle } from "../types";

interface QuickActionsProps {
  disabled: boolean;
  onRun: (prompt: string, style: JokeStyle) => void;
}

export function QuickActions({ disabled, onRun }: QuickActionsProps) {
  return (
    <section className="panel">
      <div className="panel-heading compact">
        <h2>Quick starts</h2>
      </div>

      <div className="action-row">
        {QUICK_ACTIONS.map((action) => (
          <button
            key={action.label}
            type="button"
            className="action-button"
            onClick={() => onRun(action.prompt, action.style)}
            disabled={disabled}
          >
            {action.label}
          </button>
        ))}
      </div>
    </section>
  );
}
