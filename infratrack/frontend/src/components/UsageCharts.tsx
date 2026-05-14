import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { UsageResponse, fetchUsage } from "../utils/api";

interface Props {
  teamId: number;
  period: string;
}

const CHART_COLORS = ["#8cc7ff", "#22d3ee", "#a78bfa", "#4ade80", "#f87171", "#fbbf24", "#f472b6"];

const UsageCharts = ({ teamId, period }: Props) => {
  const [usage, setUsage] = useState<UsageResponse | null>(null);

  useEffect(() => {
    fetchUsage(teamId, period)
      .then(setUsage)
      .catch(() => setUsage(null));
  }, [teamId, period]);

  if (!usage) {
    return (
      <section className="card">
        <h2>Usage</h2>
        <p className="hint">Loading…</p>
      </section>
    );
  }

  // Roll up daily totals across all services for the line chart
  const dailyMap = new Map<string, number>();
  for (const p of usage.points) {
    dailyMap.set(p.timestamp, (dailyMap.get(p.timestamp) ?? 0) + p.cost_usd);
  }
  const daily = Array.from(dailyMap, ([date, cost]) => ({ date, cost: Number(cost.toFixed(2)) }));

  const byService = Object.entries(usage.by_service)
    .map(([service, cost]) => ({ service, cost }))
    .sort((a, b) => b.cost - a.cost);

  return (
    <section className="card">
      <h2>Usage</h2>
      <p className="hint">Daily spend and breakdown by service.</p>

      <div style={{ height: 200 }}>
        <ResponsiveContainer>
          <LineChart data={daily} margin={{ top: 8, right: 8, bottom: 0, left: -10 }}>
            <CartesianGrid stroke="#1f2c4a" strokeDasharray="3 3" />
            <XAxis dataKey="date" stroke="#9aa6b2" fontSize={11} />
            <YAxis stroke="#9aa6b2" fontSize={11} />
            <Tooltip
              contentStyle={{ background: "#111a2e", border: "1px solid #1f2c4a" }}
              labelStyle={{ color: "#e6eef9" }}
            />
            <Line type="monotone" dataKey="cost" stroke="#8cc7ff" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div style={{ height: 200, marginTop: 12 }}>
        <ResponsiveContainer>
          <BarChart data={byService} margin={{ top: 8, right: 8, bottom: 0, left: -10 }}>
            <CartesianGrid stroke="#1f2c4a" strokeDasharray="3 3" />
            <XAxis dataKey="service" stroke="#9aa6b2" fontSize={11} />
            <YAxis stroke="#9aa6b2" fontSize={11} />
            <Tooltip
              contentStyle={{ background: "#111a2e", border: "1px solid #1f2c4a" }}
              labelStyle={{ color: "#e6eef9" }}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Bar dataKey="cost" fill={CHART_COLORS[0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
};

export default UsageCharts;
