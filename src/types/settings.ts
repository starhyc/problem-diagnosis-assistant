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
}

export interface SkillPackage {
  id: string;
  name: string;
  enabled: boolean;
  description?: string;
  version: string;
  entrypoint: string;
  permissions: Record<string, boolean | number | string>;
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
