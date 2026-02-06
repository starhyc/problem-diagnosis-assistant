import { create } from 'zustand';
import { LLMProvider, DatabaseConfig, TestResult, Tool } from '@/types/settings';
import { settingsApi } from '@/lib/api';

interface SettingsState {
  llmProviders: LLMProvider[];
  databases: DatabaseConfig[];
  tools: Tool[];
  loading: boolean;
  error: string | null;

  loadLLMProviders: () => Promise<void>;
  addLLMProvider: (provider: Omit<LLMProvider, 'id'>) => Promise<void>;
  updateLLMProvider: (id: string, provider: Partial<LLMProvider>) => Promise<void>;
  deleteLLMProvider: (id: string) => Promise<void>;
  testLLMProvider: (id: string) => Promise<TestResult>;
  fetchModels: (id: string) => Promise<string[]>;

  loadDatabases: () => Promise<void>;
  updateDatabase: (id: string, config: Partial<DatabaseConfig>) => Promise<void>;
  testDatabase: (id: string) => Promise<TestResult>;

  loadTools: () => Promise<void>;
  testTool: (id: string) => Promise<TestResult>;
}

export const useSettingsStore = create<SettingsState>((set, get) => ({
  llmProviders: [],
  databases: [],
  tools: [],
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

  loadDatabases: async () => {
    set({ loading: true, error: null });
    try {
      const databases = await settingsApi.getDatabases();
      set({ databases, loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
    }
  },

  updateDatabase: async (id, config) => {
    set({ loading: true, error: null });
    try {
      const updated = await settingsApi.updateDatabase(id, config);
      set(state => ({
        databases: state.databases.map(d => d.id === id ? updated : d),
        loading: false
      }));
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  testDatabase: async (id) => {
    return await settingsApi.testDatabase(id);
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
}));
