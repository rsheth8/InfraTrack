import { useEffect, useState } from "react";

import AlertsSettings from "./components/AlertsSettings";
import Dashboard from "./components/Dashboard";
import TeamSelector from "./components/TeamSelector";
import UsageCharts from "./components/UsageCharts";
import { fetchTeams, Team } from "./utils/api";

const App = () => {
  const [teams, setTeams] = useState<Team[]>([]);
  const [teamId, setTeamId] = useState<number | null>(null);
  const [period, setPeriod] = useState<string>("week");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTeams()
      .then((rows) => {
        setTeams(rows);
        if (rows.length > 0) setTeamId(rows[0].id);
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  return (
    <main>
      <h1>InfraTrack</h1>
      <p className="subtitle">Cloud spend, usage, and budget alerts across teams.</p>

      <div className="toolbar">
        <TeamSelector teams={teams} teamId={teamId} onChange={setTeamId} />
        <label htmlFor="period">Period</label>
        <select
          id="period"
          value={period}
          onChange={(e) => setPeriod(e.target.value)}
        >
          <option value="day">Today</option>
          <option value="week">Last 7 days</option>
          <option value="month">Last 30 days</option>
          <option value="quarter">Last 90 days</option>
        </select>
      </div>

      {error && <p className="error">{error}</p>}

      {teamId !== null && (
        <>
          <Dashboard teamId={teamId} period={period} />
          <div style={{ height: 20 }} />
          <div className="grid">
            <UsageCharts teamId={teamId} period={period} />
            <AlertsSettings teamId={teamId} />
          </div>
        </>
      )}
    </main>
  );
};

export default App;
