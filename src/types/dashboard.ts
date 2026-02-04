export interface DashboardStats {
  active_tasks: number;
  success_rate: number;
  avg_resolution_time: string;
  total_cases: number;
}

export interface Case {
  id: string;
  symptom: string;
  status: string;
  lead_agent: string;
  timestamp: string;
  confidence: number;
}

export interface SystemHealth {
  name: string;
  status: string;
  latency: string;
}

export interface DashboardData {
  stats: DashboardStats;
  recent_cases: Case[];
  system_health: Record<string, SystemHealth>;
  agents: Agent[];
}
