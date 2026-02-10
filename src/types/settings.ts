export interface Tool {
  id: string;
  name: string;
  connected: boolean;
  url: string;
}

export interface LLMProvider {
  id: string;
  name: string;
  provider: string;
  api_key: string;
  base_url?: string;
  models: string[];
  is_default: boolean;
  enabled: boolean;
}

export interface MCPServer {
  id: string;
  name: string;
  transport: string;
  endpoint: string;
  enabled: boolean;
  version: string;
  status?: string;
  last_test_at?: string;
  last_test_status?: string;
  created_by?: string;
  updated_by?: string;
  updated_at?: string;
}

export interface SkillPackage {
  id: string;
  name: string;
  enabled: boolean;
  description?: string;
  version: string;
  entrypoint: string;
  permissions: Record<string, boolean | number | string>;
  status?: string;
  last_test_at?: string;
  last_test_status?: string;
  created_by?: string;
  updated_by?: string;
  updated_at?: string;
}

export interface ManagedUser {
  id: number;
  username: string;
  email: string;
  display_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface AuditEntry {
  id: string;
  module: string;
  action: string;
  actor: string;
  target_id: string;
  detail: Record<string, any>;
  timestamp: string;
}

export interface TestResult {
  success: boolean;
  message: string;
}

export interface SettingsData {
  tools: Tool[];
  llmProviders: LLMProvider[];
  mcpServers: MCPServer[];
  skills: SkillPackage[];
}
