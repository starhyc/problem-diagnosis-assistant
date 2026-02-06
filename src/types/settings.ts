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
  is_primary: boolean;
  is_fallback: boolean;
  enabled: boolean;
}

export interface DatabaseConfig {
  id: string;
  type: string;
  host?: string;
  port?: number;
  database?: string;
  user?: string;
  password?: string;
  url?: string;
}

export interface TestResult {
  success: boolean;
  message: string;
}

export interface SettingsData {
  tools: Tool[];
  llmProviders: LLMProvider[];
  databases: DatabaseConfig[];
}
