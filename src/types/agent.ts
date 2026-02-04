import { FileSearch, MessageSquare, Code, Brain } from 'lucide-react';

export interface Agent {
  id: string;
  name: string;
  role: string;
  color: string;
  description: string;
}

export type AgentType = 'diagnosis' | 'qa' | 'log_analysis';

export type ModelType = 'gpt-4' | 'gpt-3.5-turbo' | 'claude-3' | 'qwen-max' | 'deepseek-chat';

export interface AgentTypeInfo {
  id: AgentType;
  name: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  fileInputs: FileInputConfig[];
}

export interface ModelInfo {
  id: ModelType;
  name: string;
  provider: string;
  description: string;
}

export interface FileInputConfig {
  id: string;
  label: string;
  accept: string;
  multiple: boolean;
  optional: boolean;
}

export const AGENT_TYPES: AgentTypeInfo[] = [
  {
    id: 'diagnosis',
    name: '诊断类型',
    description: '多Agent协同问题诊断',
    icon: FileSearch,
    fileInputs: [
      { id: 'scenario', label: '场景文件', accept: '.json,.yaml,.yml', multiple: false, optional: false },
      { id: 'input', label: '输入文件', accept: '.log,.txt', multiple: true, optional: false },
      { id: 'output', label: '输出文件', accept: '.log,.txt', multiple: true, optional: true },
      { id: 'config', label: '配置文件', accept: '.yml,.yaml,.properties', multiple: true, optional: true },
    ],
  },
  {
    id: 'qa',
    name: '问答类型',
    description: '智能问答助手',
    icon: MessageSquare,
    fileInputs: [
      { id: 'document', label: '文档文件', accept: '.pdf,.doc,.docx,.txt', multiple: true, optional: true },
    ],
  },
  {
    id: 'log_analysis',
    name: '日志分析',
    description: '日志文件分析',
    icon: Code,
    fileInputs: [
      { id: 'logs', label: '日志文件', accept: '.log,.txt', multiple: true, optional: false },
      { id: 'config', label: '配置文件', accept: '.yml,.yaml,.properties', multiple: true, optional: true },
    ],
  },
];

export const MODEL_TYPES: ModelInfo[] = [
  {
    id: 'gpt-4',
    name: 'GPT-4',
    provider: 'OpenAI',
    description: '最强大的通用大模型',
  },
  {
    id: 'gpt-3.5-turbo',
    name: 'GPT-3.5 Turbo',
    provider: 'OpenAI',
    description: '快速响应的通用大模型',
  },
  {
    id: 'claude-3',
    name: 'Claude 3',
    provider: 'Anthropic',
    description: '擅长分析和推理的大模型',
  },
  {
    id: 'qwen-max',
    name: '通义千问 Max',
    provider: '阿里云',
    description: '中文优化的通用大模型',
  },
  {
    id: 'deepseek-chat',
    name: 'DeepSeek Chat',
    provider: 'DeepSeek',
    description: '性价比高的开源大模型',
  },
];
