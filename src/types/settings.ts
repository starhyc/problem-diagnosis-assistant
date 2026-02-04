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
