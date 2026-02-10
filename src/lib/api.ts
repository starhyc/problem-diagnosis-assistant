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

export interface HistoryEvent {
  sequence: number;
  event_type: string;
  event_data: Record<string, any>;
  timestamp: string;
}

export interface HistorySession {
  session_id: string;
  snapshot_version: number;
  current_phase: string;
  confidence: number;
  message_count: number;
  event_count: number;
  service?: string;
  problem_type?: string;
  updated_at: string;
}

export interface HistoryDetail {
  session_id: string;
  snapshot_version: number;
  snapshot_data: Record<string, any>;
  event_count: number;
  first_event_at?: string;
  last_event_at?: string;
  events: HistoryEvent[];
}

export interface HistoricalCasePayload {
  case_id: string;
  title: string;
  symptoms: string[];
  root_cause: string;
  solution: string;
  confidence: number;
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
  tools: Tool[];
}


export interface MCPServer {
  id: string;
  name: string;
  transport: string;
  endpoint: string;
  enabled: boolean;
  version: string;
}

export interface SkillPackage {
  id: string;
  name: string;
  enabled: boolean;
  description?: string;
  version: string;
  entrypoint: string;
  permissions: Record<string, any>;
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
    ...options.headers,
  };

  const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData;
  if (!isFormData) {
    headers['Content-Type'] = 'application/json';
  }

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
    context?: any,
    mode: string = 'auto'
  ): Promise<any> {
    return request('/investigation/start', {
      method: 'POST',
      body: JSON.stringify({
        agent_type: agentType,
        problem_description: problemDescription,
        description,
        files,
        context,
        mode,
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

export const historyApi = {
  async getSessions(params?: {
    start_time?: string;
    end_time?: string;
    service?: string;
    problem_type?: string;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
  }): Promise<HistorySession[]> {
    const query = new URLSearchParams();
    if (params?.start_time) query.set('start_time', params.start_time);
    if (params?.end_time) query.set('end_time', params.end_time);
    if (params?.service) query.set('service', params.service);
    if (params?.problem_type) query.set('problem_type', params.problem_type);
    if (params?.sort_by) query.set('sort_by', params.sort_by);
    if (params?.sort_order) query.set('sort_order', params.sort_order);
    const suffix = query.toString() ? `?${query.toString()}` : '';
    return request<HistorySession[]>(`/history${suffix}`);
  },

  async getSessionDetail(sessionId: string): Promise<HistoryDetail> {
    return request<HistoryDetail>(`/history/${sessionId}`);
  },

  async getSessionEvents(sessionId: string): Promise<HistoryEvent[]> {
    return request<HistoryEvent[]>(`/history/${sessionId}/events`);
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

  async createHistoricalCase(payload: HistoricalCasePayload): Promise<HistoricalCase> {
    return request<HistoricalCase>('/knowledge/cases', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async updateHistoricalCase(caseId: string, payload: Partial<HistoricalCasePayload>): Promise<HistoricalCase> {
    return request<HistoricalCase>(`/knowledge/cases/${caseId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  },

  async deleteHistoricalCase(caseId: string): Promise<{ status: string; case_id: string }> {
    return request<{ status: string; case_id: string }>(`/knowledge/cases/${caseId}`, {
      method: 'DELETE',
    });
  },
};

export const settingsApi = {
  async getLLMProviders(): Promise<any[]> {
    return request('/settings/llm-providers');
  },

  async addLLMProvider(provider: any): Promise<any> {
    return request('/settings/llm-providers', {
      method: 'POST',
      body: JSON.stringify(provider),
    });
  },

  async updateLLMProvider(id: string, provider: any): Promise<any> {
    return request(`/settings/llm-providers/${id}`, {
      method: 'PUT',
      body: JSON.stringify(provider),
    });
  },

  async deleteLLMProvider(id: string): Promise<void> {
    return request(`/settings/llm-providers/${id}`, {
      method: 'DELETE',
    });
  },

  async testLLMProvider(id: string): Promise<any> {
    return request(`/settings/llm-providers/${id}/test`, {
      method: 'POST',
    });
  },

  async fetchModels(id: string): Promise<string[]> {
    const response = await request<{ models: string[] }>(`/settings/llm-providers/${id}/models`);
    return response.models;
  },

  async discoverModels(config: { provider: string; api_key: string; base_url?: string }): Promise<string[]> {
    const response = await request<{ models: string[] }>('/settings/llm-providers/discover-models', {
      method: 'POST',
      body: JSON.stringify(config),
    });
    return response.models;
  },

  async getTools(): Promise<any[]> {
    return request('/settings/tools');
  },

  async testTool(id: string): Promise<any> {
    return request(`/settings/tools/${id}/test`, {
      method: 'POST',
    });
  },

  async getMCPServers(): Promise<MCPServer[]> {
    return request('/settings/mcp-servers');
  },

  async saveMCPServer(server: MCPServer): Promise<MCPServer> {
    return request('/settings/mcp-servers', {
      method: 'POST',
      body: JSON.stringify(server),
    });
  },

  async toggleMCPServer(id: string, enabled: boolean): Promise<MCPServer> {
    return request(`/settings/mcp-servers/${id}/enabled`, {
      method: 'PUT',
      body: JSON.stringify({ enabled }),
    });
  },

  async testMCPServer(id: string): Promise<any> {
    return request(`/settings/mcp-servers/${id}/test`, {
      method: 'POST',
    });
  },

  async getSkills(): Promise<SkillPackage[]> {
    return request('/settings/skills');
  },

  async uploadSkill(file: File): Promise<SkillPackage> {
    const form = new FormData();
    form.append('file', file);
    return request('/settings/skills/upload', {
      method: 'POST',
      body: form,
    });
  },

  async toggleSkill(id: string, enabled: boolean): Promise<SkillPackage> {
    return request(`/settings/skills/${id}/enabled`, {
      method: 'PUT',
      body: JSON.stringify({ enabled }),
    });
  },

  async executeSkill(id: string, approvalGranted: boolean): Promise<any> {
    return request(`/settings/skills/${id}/execute`, {
      method: 'POST',
      body: JSON.stringify({ approval_granted: approvalGranted }),
    });
  },
};

export { ApiError };
