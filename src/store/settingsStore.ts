import { create } from 'zustand';
import { AuditEntry, LLMProvider, MCPServer, ManagedUser, SkillPackage, TestResult, Tool } from '@/types/settings';
type LLMProviderPayload = {
  name: string;
  provider: string;
  api_key?: string;
  base_url?: string;
  models: string[];
  is_default: boolean;
  enabled: boolean;
};

import { settingsApi } from '@/lib/api';

interface SettingsState {
  llmProviders: LLMProvider[];
  tools: Tool[];
  mcpServers: MCPServer[];
  skills: SkillPackage[];
  users: ManagedUser[];
  moduleAuditLogs: Record<string, AuditEntry[]>;
  moduleRecentChanges: Record<string, AuditEntry[]>;
  loading: boolean;
  error: string | null;

  loadLLMProviders: () => Promise<void>;
  addLLMProvider: (provider: LLMProviderPayload) => Promise<void>;
  updateLLMProvider: (id: string, provider: Partial<LLMProviderPayload>) => Promise<void>;
  deleteLLMProvider: (id: string) => Promise<void>;
  testLLMProvider: (id: string) => Promise<TestResult>;
  fetchModels: (id: string) => Promise<string[]>;
  discoverModels: (config: { provider: string; api_key: string; base_url?: string }) => Promise<string[]>;

  loadTools: () => Promise<void>;
  testTool: (id: string) => Promise<TestResult>;

  loadMCPServers: () => Promise<void>;
  saveMCPServer: (server: MCPServer) => Promise<void>;
  toggleMCPServer: (id: string, enabled: boolean) => Promise<void>;
  testMCPServer: (id: string) => Promise<TestResult>;

  loadSkills: () => Promise<void>;
  uploadSkill: (file: File) => Promise<void>;
  toggleSkill: (id: string, enabled: boolean) => Promise<void>;
  executeSkill: (id: string, approvalGranted: boolean) => Promise<any>;
  testSkill: (id: string) => Promise<TestResult>;

  loadUsers: () => Promise<void>;
  createUser: (payload: { username: string; email: string; password: string; display_name: string; role: string }) => Promise<void>;
  updateUserStatus: (userId: number, isActive: boolean) => Promise<void>;
  updateUserRole: (userId: number, role: string) => Promise<void>;

  loadModuleAuditLogs: (module: string) => Promise<void>;
  loadModuleRecentChanges: (module: string) => Promise<void>;
  logSystemParamsChange: (action: string, detail: Record<string, any>) => Promise<void>;
}

export const useSettingsStore = create<SettingsState>((set, get) => ({
  llmProviders: [],
  tools: [],
  mcpServers: [],
  skills: [],
  users: [],
  moduleAuditLogs: {},
  moduleRecentChanges: {},
  loading: false,
  error: null,

  loadLLMProviders: async () => {
    set({ loading: true, error: null });
    try {
      const providers = await settingsApi.getLLMProviders();
      set({ llmProviders: providers, loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
    }
  },

  addLLMProvider: async (provider) => {
    set({ loading: true, error: null });
    try {
      const newProvider = await settingsApi.addLLMProvider(provider);
      set(state => ({ llmProviders: [...state.llmProviders, newProvider], loading: false }));
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  updateLLMProvider: async (id, provider) => {
    set({ loading: true, error: null });
    try {
      const updated = await settingsApi.updateLLMProvider(id, provider);
      set(state => ({
        llmProviders: state.llmProviders.map(p => p.id === id ? updated : p),
        loading: false
      }));
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  deleteLLMProvider: async (id) => {
    set({ loading: true, error: null });
    try {
      await settingsApi.deleteLLMProvider(id);
      set(state => ({
        llmProviders: state.llmProviders.filter(p => p.id !== id),
        loading: false
      }));
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  testLLMProvider: async (id) => {
    return await settingsApi.testLLMProvider(id);
  },

  fetchModels: async (id) => {
    return await settingsApi.fetchModels(id);
  },

  discoverModels: async (config) => {
    return await settingsApi.discoverModels(config);
  },

  loadTools: async () => {
    set({ loading: true, error: null });
    try {
      const tools = await settingsApi.getTools();
      set({ tools, loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
    }
  },

  testTool: async (id) => {
    return await settingsApi.testTool(id);
  },

  loadMCPServers: async () => {
    try {
      const mcpServers = await settingsApi.getMCPServers();
      set({ mcpServers });
    } catch (error: any) {
      set({ error: error.message });
    }
  },

  saveMCPServer: async (server) => {
    const saved = await settingsApi.saveMCPServer(server);
    set(state => ({
      mcpServers: [...state.mcpServers.filter(m => m.id !== saved.id), saved],
    }));
  },

  toggleMCPServer: async (id, enabled) => {
    const updated = await settingsApi.toggleMCPServer(id, enabled);
    set(state => ({
      mcpServers: state.mcpServers.map(m => (m.id === id ? updated : m)),
    }));
  },

  testMCPServer: async (id) => {
    return await settingsApi.testMCPServer(id);
  },

  loadSkills: async () => {
    try {
      const skills = await settingsApi.getSkills();
      set({ skills });
    } catch (error: any) {
      set({ error: error.message });
    }
  },

  uploadSkill: async (file) => {
    const uploaded = await settingsApi.uploadSkill(file);
    set(state => ({
      skills: [...state.skills.filter(s => s.id !== uploaded.id), uploaded],
    }));
  },

  toggleSkill: async (id, enabled) => {
    const updated = await settingsApi.toggleSkill(id, enabled);
    set(state => ({
      skills: state.skills.map(s => (s.id === id ? updated : s)),
    }));
  },

  executeSkill: async (id, approvalGranted) => {
    return await settingsApi.executeSkill(id, approvalGranted);
  },

  testSkill: async (id) => {
    return await settingsApi.testSkill(id);
  },

  loadUsers: async () => {
    try {
      const users = await settingsApi.getUsers();
      set({ users });
    } catch (error: any) {
      set({ error: error.message });
    }
  },

  createUser: async (payload) => {
    const created = await settingsApi.createUser(payload);
    set(state => ({ users: [...state.users, created] }));
  },

  updateUserStatus: async (userId, isActive) => {
    const updated = await settingsApi.updateUserStatus(userId, isActive);
    set(state => ({ users: state.users.map(u => u.id === userId ? updated : u) }));
  },

  updateUserRole: async (userId, role) => {
    const updated = await settingsApi.updateUserRole(userId, role);
    set(state => ({ users: state.users.map(u => u.id === userId ? updated : u) }));
  },

  loadModuleAuditLogs: async (module) => {
    const logs = await settingsApi.getModuleAuditLogs(module);
    set(state => ({ moduleAuditLogs: { ...state.moduleAuditLogs, [module]: logs } }));
  },

  loadModuleRecentChanges: async (module) => {
    const changes = await settingsApi.getModuleRecentChanges(module);
    set(state => ({ moduleRecentChanges: { ...state.moduleRecentChanges, [module]: changes } }));
  },

  logSystemParamsChange: async (action, detail) => {
    await settingsApi.logSystemParamsChange(action, detail);
  },
}));
