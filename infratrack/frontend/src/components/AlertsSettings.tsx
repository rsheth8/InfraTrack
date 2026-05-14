import { FormEvent, useEffect, useState } from "react";

import { Alert, createAlert, deleteAlert, fetchAlerts } from "../utils/api";

interface Props {
  teamId: number;
}

const AlertsSettings = ({ teamId }: Props) => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [threshold, setThreshold] = useState<number>(80);
  const [email, setEmail] = useState<string>("");
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = () => {
    fetchAlerts(teamId)
      .then(setAlerts)
      .catch((err: Error) => setError(err.message));
  };

  useEffect(() => {
    refresh();
  }, [teamId]);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!email.includes("@")) {
      setError("Enter a valid email");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await createAlert({ team_id: teamId, threshold, email });
      setEmail("");
      refresh();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSubmitting(false);
    }
  };

  const onDelete = async (id: number) => {
    try {
      await deleteAlert(id);
      refresh();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <section className="card">
      <h2>Alerts</h2>
      <p className="hint">Trigger email when monthly spend crosses a percentage of budget.</p>

      <form onSubmit={onSubmit} style={{ display: "flex", gap: 8, marginBottom: 12 }}>
        <input
          type="number"
          min={1}
          max={200}
          value={threshold}
          onChange={(e) => setThreshold(Number(e.target.value))}
          style={{ width: 80 }}
          aria-label="Threshold percent"
        />
        <input
          type="email"
          placeholder="oncall@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={{ flex: 1 }}
          aria-label="Email"
        />
        <button className="btn" type="submit" disabled={submitting}>
          Add
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      <ul className="alerts-list">
        {alerts.length === 0 && <li style={{ justifyContent: "center" }}>No alerts yet</li>}
        {alerts.map((a) => (
          <li key={a.id}>
            <span>
              <strong>{a.threshold.toFixed(0)}%</strong> · {a.email}
            </span>
            <button
              onClick={() => onDelete(a.id)}
              style={{
                background: "transparent",
                color: "var(--muted)",
                border: 0,
                cursor: "pointer",
              }}
              aria-label={`Delete alert ${a.id}`}
            >
              remove
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
};

export default AlertsSettings;
