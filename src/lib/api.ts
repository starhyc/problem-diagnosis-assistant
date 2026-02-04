const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: {
    id: number;
    username: string;
    email: string;
    display_name: string;
    role: string;
    avatar?: string;
    is_active: boolean;
    created_at: string;
  };
}

export interface UserResponse {
  id: number;
  username: string;
  email: string;
  display_name: string;
  role: string;
  avatar?: string;
  is_active: boolean;
  created_at: string;
}

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

export interface Agent {
  id: string;
  name: string;
  role: string;
  color: string;
  description: string;
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

export interface TopologyNode {
  id: string;
  label: string;
  type: string;
  status: string;
}

export interface TopologyEdge {
  source: string;
  target: string;
}

export interface HypothesisNode {
  id: string;
  label: string;
  type: string;
  probability?: number;
  status?: string;
  evidence?: string[];
}

export interface HypothesisTree {
  root: HypothesisNode;
}

export interface InvestigationData {
  agents: Agent[];
  sample_logs: string;
  topology_nodes: TopologyNode[];
  topology_edges: TopologyEdge[];
  hypothesis_tree: HypothesisTree;
}

export interface KnowledgeNode {
  id: string;
  type: string;
  label: string;
  x: number;
  y: number;
}

export interface KnowledgeEdge {
  source: string;
  target: string;
  label: string;
}

export interface KnowledgeGraph {
  nodes: KnowledgeNode[];
  edges: KnowledgeEdge[];
}

export interface HistoricalCase {
  id: string;
  title: string;
  symptoms: string[];
  root_cause: string;
  solution: string;
  confidence: number;
  hits: number;
  last_used: string;
}

export interface KnowledgeData {
  graph: KnowledgeGraph;
  historical_cases: HistoricalCase[];
}

export interface Redline {
  id: string;
  name: string;
  enabled: boolean;
  description: string;
}

export interface Tool {
  id: string;
  name: string;
  connected: boolean;
  url: string;
}

export interface MaskingRule {
  pattern: string;
  name: string;
  replacement: string;
}

export interface SettingsData {
  redlines: Redline[];
  tools: Tool[];
  masking_rules: MaskingRule[];
}

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem('aiops_token');
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '请求失败' }));
    throw new ApiError(response.status, error.detail || '请求失败');
  }

  return response.json();
}

export const authApi = {
  async login(data: LoginRequest): Promise<LoginResponse> {
    return request<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async getCurrentUser(): Promise<UserResponse> {
    return request<UserResponse>('/auth/me');
  },

  async logout(): Promise<{ message: string }> {
    return request<{ message: string }>('/auth/logout', {
      method: 'POST',
    });
  },

  async register(data: {
    username: string;
    email: string;
    password: string;
    display_name: string;
    role?: string;
  }): Promise<UserResponse> {
    return request<UserResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
};

export const dashboardApi = {
  async getDashboardData(): Promise<DashboardData> {
    return request<DashboardData>('/dashboard');
  },

  async getStats(): Promise<DashboardStats> {
    return request<DashboardStats>('/dashboard/stats');
  },

  async getRecentCases(skip: number = 0, limit: number = 10): Promise<Case[]> {
    return request<Case[]>(`/dashboard/cases?skip=${skip}&limit=${limit}`);
  },

  async getAgents(): Promise<Agent[]> {
    return request<Agent[]>('/dashboard/agents');
  },

  async getSystemHealth(): Promise<Record<string, SystemHealth>> {
    return request<Record<string, SystemHealth>>('/dashboard/system-health');
  },
};

export const investigationApi = {
  async getInvestigationData(): Promise<InvestigationData> {
    return request<InvestigationData>('/investigation');
  },

  async startDiagnosis(
    agentType: string,
    problemDescription: string,
    description?: string,
    files?: Record<string, string[]>,
    context?: any
  ): Promise<any> {
    return request('/investigation/start', {
      method: 'POST',
      body: JSON.stringify({
        agent_type: agentType,
        problem_description: problemDescription,
        description,
        files,
        context,
      }),
    });
  },

  async stopDiagnosis(): Promise<any> {
    return request('/investigation/stop', {
      method: 'POST',
    });
  },

  async getProposedAction(): Promise<{ title: string; confidence: number; description: string }> {
    return request('/investigation/action');
  },

  async approveAction(): Promise<any> {
    return request('/investigation/action/approve', {
      method: 'POST',
    });
  },

  async rejectAction(): Promise<any> {
    return request('/investigation/action/reject', {
      method: 'POST',
    });
  },
};

export const knowledgeApi = {
  async getKnowledgeData(): Promise<KnowledgeData> {
    return request<KnowledgeData>('/knowledge');
  },

  async getKnowledgeGraph(): Promise<KnowledgeGraph> {
    return request<KnowledgeGraph>('/knowledge/graph');
  },

  async getHistoricalCases(): Promise<HistoricalCase[]> {
    return request<HistoricalCase[]>('/knowledge/cases');
  },

  async getHistoricalCase(caseId: string): Promise<HistoricalCase> {
    return request<HistoricalCase>(`/knowledge/cases/${caseId}`);
  },
};

export const settingsApi = {
  async getSettings(): Promise<SettingsData> {
    return request<SettingsData>('/settings');
  },

  async updateRedline(redlineId: string, enabled: boolean): Promise<any> {
    return request(`/settings/redlines/${redlineId}`, {
      method: 'PUT',
      body: JSON.stringify({ enabled }),
    });
  },

  async testToolConnection(toolId: string): Promise<any> {
    return request(`/settings/tools/${toolId}/test`, {
      method: 'POST',
    });
  },

  async testMasking(text: string): Promise<{ original: string; masked: string }> {
    return request('/settings/mask', {
      method: 'POST',
      body: JSON.stringify({ text }),
    });
  },
};

export { ApiError };
