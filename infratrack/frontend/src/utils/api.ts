export const apiBaseUrl = "/api";

export interface Team {
  id: number;
  name: string;
}

export interface UsagePoint {
  timestamp: string;
  service: string;
  cost_usd: number;
}

export interface UsageResponse {
  team_id: number;
  period: string;
  total_usd: number;
  points: UsagePoint[];
  by_service: Record<string, number>;
}

export interface BudgetResponse {
  team_id: number;
  month: string;
  budget_usd: number;
  spend_usd: number;
  percent_used: number;
}

export interface Alert {
  id: number;
  team_id: number;
  threshold: number;
  email: string;
  enabled: boolean;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${apiBaseUrl}${path}`);
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
  return res.json() as Promise<T>;
}

export const fetchTeams = () => get<Team[]>(`/teams`);

export const fetchUsage = (teamId: number, period: string) =>
  get<UsageResponse>(`/usage?team_id=${teamId}&period=${period}`);

export const fetchBudget = (teamId: number) =>
  get<BudgetResponse>(`/budget?team_id=${teamId}`);

export const fetchAlerts = (teamId: number) =>
  get<Alert[]>(`/alerts?team_id=${teamId}`);

export const createAlert = async (payload: {
  team_id: number;
  threshold: number;
  email: string;
}): Promise<Alert> => {
  const res = await fetch(`${apiBaseUrl}/alerts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`POST /alerts failed: ${res.status}`);
  return res.json();
};

export const deleteAlert = async (alertId: number): Promise<void> => {
  const res = await fetch(`${apiBaseUrl}/alerts/${alertId}`, {
    method: "DELETE",
  });
  if (!res.ok && res.status !== 204) {
    throw new Error(`DELETE /alerts/${alertId} failed: ${res.status}`);
  }
};
