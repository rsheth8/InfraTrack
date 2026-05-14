import { useEffect, useState } from "react";

import { BudgetResponse, UsageResponse, fetchBudget, fetchUsage } from "../utils/api";

interface Props {
  teamId: number;
  period: string;
}

const Dashboard = ({ teamId, period }: Props) => {
  const [usage, setUsage] = useState<UsageResponse | null>(null);
  const [budget, setBudget] = useState<BudgetResponse | null>(null);

  useEffect(() => {
    Promise.all([fetchUsage(teamId, period), fetchBudget(teamId)])
      .then(([u, b]) => {
        setUsage(u);
        setBudget(b);
      })
      .catch(() => {
        setUsage(null);
        setBudget(null);
      });
  }, [teamId, period]);

  if (!usage || !budget) {
    return (
      <section className="card">
        <h2>Overview</h2>
        <p className="hint">Loading…</p>
      </section>
    );
  }

  const over = budget.percent_used > 100;

  return (
    <section className="card">
      <h2>Overview</h2>
      <p className="hint">
        Spend snapshot for team #{teamId} · {period}
      </p>

      <div className="stat-row">
        <div>
          <div className="stat-label">Period total</div>
          <div className="stat">${usage.total_usd.toLocaleString()}</div>
        </div>
        <div>
          <div className="stat-label">{budget.month} budget</div>
          <div className="stat">
            ${budget.spend_usd.toLocaleString()}{" "}
            <span style={{ color: "var(--muted)", fontSize: 14 }}>
              / ${budget.budget_usd.toLocaleString()}
            </span>
          </div>
        </div>
        <div>
          <div className="stat-label">Used</div>
          <div className="stat" style={{ color: over ? "var(--danger)" : undefined }}>
            {budget.percent_used.toFixed(1)}%
          </div>
        </div>
      </div>

      <div className="bar-wrap">
        <div
          className={`bar-fill${over ? " over" : ""}`}
          style={{ width: `${Math.min(100, budget.percent_used)}%` }}
        />
      </div>
    </section>
  );
};

export default Dashboard;
