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

export interface TestResult {
  success: boolean;
  message: string;
}

export interface SettingsData {
  tools: Tool[];
  llmProviders: LLMProvider[];
}
