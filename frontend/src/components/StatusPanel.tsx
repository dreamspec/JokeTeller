import type { StatusResponse } from "../types";

interface StatusPanelProps {
  status: StatusResponse | null;
  statusError: string | null;
  loading: boolean;
  onRefresh: () => void;
}

export function StatusPanel({ status, statusError, loading, onRefresh }: StatusPanelProps) {
  const lmStatus = status?.lm_studio;
  const backendHealthy = Boolean(status) && !statusError;

  return (
    <section className="panel surface-card status-panel">
      <div className="panel-heading">
        <h2>System status</h2>
        <button className="ghost-button" type="button" onClick={onRefresh} disabled={loading}>
          {loading ? "Checking..." : "Refresh"}
        </button>
      </div>

      <div className="status-grid">
        <div className={`status-pill ${backendHealthy ? "status-pill-ok" : "status-pill-warn"}`}>
          {backendHealthy ? "Backend reachable" : "Backend unreachable"}
        </div>
        <div className={`status-pill ${lmStatus?.reachable ? "status-pill-ok" : "status-pill-warn"}`}>
          {lmStatus?.reachable ? "LM Studio reachable" : "LM Studio unreachable"}
        </div>
      </div>

      {statusError ? <p className="status-note status-note-error">{statusError}</p> : null}
      {!statusError && lmStatus?.error ? <p className="status-note">{lmStatus.error}</p> : null}
      {lmStatus?.available_models.length ? (
        <p className="status-note">Models: <strong>{lmStatus.available_models.join(", ")}</strong></p>
      ) : null}
    </section>
  );
}
