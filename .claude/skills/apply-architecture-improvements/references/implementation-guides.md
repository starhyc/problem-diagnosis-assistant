# Implementation Guides

Detailed step-by-step guides for implementing common architectural patterns.

## Guide 1: Implementing Multi-Provider LLM Abstraction

### Overview
Create a flexible LLM provider system that supports multiple providers (OpenAI, Anthropic, etc.) with automatic fallback.

### Step-by-Step Implementation

#### Step 1: Create Directory Structure
```bash
mkdir -p src/lib/llm/providers
touch src/lib/llm/types.ts
touch src/lib/llm/factory.ts
touch src/lib/llm/providers/openai.ts
touch src/lib/llm/providers/anthropic.ts
```

#### Step 2: Define Provider Interface
**File:** `src/lib/llm/types.ts`

```typescript
export interface LLMProvider {
  name: string;
  generate(prompt: string, options?: GenerateOptions): Promise<string>;
  stream(prompt: string, options?: StreamOptions): AsyncIterator<string>;
  countTokens(text: string): number;
}

export interface GenerateOptions {
  temperature?: number;
  maxTokens?: number;
  stopSequences?: string[];
}

export interface StreamOptions extends GenerateOptions {
  onChunk?: (chunk: string) => void;
}

export interface LLMConfig {
  provider: 'openai' | 'anthropic';
  apiKey: string;
  model?: string;
  fallbackProvider?: 'openai' | 'anthropic';
}
```

#### Step 3: Implement OpenAI Provider
**File:** `src/lib/llm/providers/openai.ts`

```typescript
import OpenAI from 'openai';
import { LLMProvider, GenerateOptions, StreamOptions } from '../types';

export class OpenAIProvider implements LLMProvider {
  name = 'openai';
  private client: OpenAI;
  private model: string;

  constructor(apiKey: string, model = 'gpt-4') {
    this.client = new OpenAI({ apiKey });
    this.model = model;
  }

  async generate(prompt: string, options?: GenerateOptions): Promise<string> {
    const response = await this.client.chat.completions.create({
      model: this.model,
      messages: [{ role: 'user', content: prompt }],
      temperature: options?.temperature,
      max_tokens: options?.maxTokens,
      stop: options?.stopSequences,
    });
    return response.choices[0]?.message?.content || '';
  }

  async *stream(prompt: string, options?: StreamOptions): AsyncIterator<string> {
    const stream = await this.client.chat.completions.create({
      model: this.model,
      messages: [{ role: 'user', content: prompt }],
      temperature: options?.temperature,
      max_tokens: options?.maxTokens,
      stop: options?.stopSequences,
      stream: true,
    });

    for await (const chunk of stream) {
      const content = chunk.choices[0]?.delta?.content || '';
      if (content) {
        options?.onChunk?.(content);
        yield content;
      }
    }
  }

  countTokens(text: string): number {
    // Rough estimation: ~4 chars per token
    return Math.ceil(text.length / 4);
  }
}
```

#### Step 4: Implement Anthropic Provider
**File:** `src/lib/llm/providers/anthropic.ts`

```typescript
import Anthropic from '@anthropic-ai/sdk';
import { LLMProvider, GenerateOptions, StreamOptions } from '../types';

export class AnthropicProvider implements LLMProvider {
  name = 'anthropic';
  private client: Anthropic;
  private model: string;

  constructor(apiKey: string, model = 'claude-3-5-sonnet-20241022') {
    this.client = new Anthropic({ apiKey });
    this.model = model;
  }

  async generate(prompt: string, options?: GenerateOptions): Promise<string> {
    const response = await this.client.messages.create({
      model: this.model,
      max_tokens: options?.maxTokens || 1024,
      messages: [{ role: 'user', content: prompt }],
      temperature: options?.temperature,
      stop_sequences: options?.stopSequences,
    });
    return response.content[0].type === 'text' ? response.content[0].text : '';
  }

  async *stream(prompt: string, options?: StreamOptions): AsyncIterator<string> {
    const stream = await this.client.messages.create({
      model: this.model,
      max_tokens: options?.maxTokens || 1024,
      messages: [{ role: 'user', content: prompt }],
      temperature: options?.temperature,
      stop_sequences: options?.stopSequences,
      stream: true,
    });

    for await (const event of stream) {
      if (event.type === 'content_block_delta' && event.delta.type === 'text_delta') {
        const content = event.delta.text;
        options?.onChunk?.(content);
        yield content;
      }
    }
  }

  countTokens(text: string): number {
    // Rough estimation: ~4 chars per token
    return Math.ceil(text.length / 4);
  }
}
```

#### Step 5: Create Factory with Fallback
**File:** `src/lib/llm/factory.ts`

```typescript
import { LLMProvider, LLMConfig } from './types';
import { OpenAIProvider } from './providers/openai';
import { AnthropicProvider } from './providers/anthropic';

export class LLMFactory {
  private static providers = new Map<string, LLMProvider>();

  static create(config: LLMConfig): LLMProvider {
    const key = `${config.provider}-${config.model || 'default'}`;

    if (this.providers.has(key)) {
      return this.providers.get(key)!;
    }

    const provider = this.createProvider(config);
    this.providers.set(key, provider);
    return provider;
  }

  private static createProvider(config: LLMConfig): LLMProvider {
    switch (config.provider) {
      case 'openai':
        return new OpenAIProvider(config.apiKey, config.model);
      case 'anthropic':
        return new AnthropicProvider(config.apiKey, config.model);
      default:
        throw new Error(`Unknown provider: ${config.provider}`);
    }
  }

  static async generateWithFallback(
    config: LLMConfig,
    prompt: string
  ): Promise<string> {
    try {
      const provider = this.create(config);
      return await provider.generate(prompt);
    } catch (error) {
      if (config.fallbackProvider && config.fallbackProvider !== config.provider) {
        console.warn(`Primary provider failed, trying fallback: ${config.fallbackProvider}`);
        const fallbackConfig = { ...config, provider: config.fallbackProvider };
        const fallbackProvider = this.create(fallbackConfig);
        return await fallbackProvider.generate(prompt);
      }
      throw error;
    }
  }
}
```

#### Step 6: Migrate Existing Code
**Before:**
```typescript
import OpenAI from 'openai';

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
const response = await openai.chat.completions.create({
  model: 'gpt-4',
  messages: [{ role: 'user', content: prompt }],
});
const result = response.choices[0].message.content;
```

**After:**
```typescript
import { LLMFactory } from '@/lib/llm/factory';

const llm = LLMFactory.create({
  provider: 'openai',
  apiKey: process.env.OPENAI_API_KEY!,
  fallbackProvider: 'anthropic',
});
const result = await llm.generate(prompt);
```

#### Step 7: Add Configuration
**File:** `.env`
```
LLM_PRIMARY_PROVIDER=anthropic
LLM_FALLBACK_PROVIDER=openai
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

**File:** `src/config/llm.ts`
```typescript
import { LLMConfig } from '@/lib/llm/types';

export const llmConfig: LLMConfig = {
  provider: (process.env.LLM_PRIMARY_PROVIDER as any) || 'anthropic',
  apiKey: process.env.ANTHROPIC_API_KEY || process.env.OPENAI_API_KEY || '',
  fallbackProvider: (process.env.LLM_FALLBACK_PROVIDER as any),
};
```

---

## Guide 2: Implementing WebSocket Manager

### Overview
Create a centralized WebSocket manager with reconnection logic and message routing.

### Step-by-Step Implementation

#### Step 1: Create Directory Structure
```bash
mkdir -p src/lib/websocket
touch src/lib/websocket/manager.ts
touch src/lib/websocket/types.ts
```

#### Step 2: Define Message Types
**File:** `src/lib/websocket/types.ts`

```typescript
export type MessageType =
  | 'agent_message'
  | 'action_proposal'
  | 'diagnosis_status'
  | 'timeline_update'
  | 'error';

export interface WebSocketMessage {
  type: MessageType;
  payload: any;
  timestamp: number;
}

export interface MessageHandler {
  (message: WebSocketMessage): void;
}

export interface WebSocketConfig {
  url: string;
  reconnect?: boolean;
  maxRetries?: number;
  retryDelay?: number;
}
```

#### Step 3: Implement WebSocket Manager
**File:** `src/lib/websocket/manager.ts`

```typescript
import { WebSocketConfig, WebSocketMessage, MessageHandler, MessageType } from './types';

export class WebSocketManager {
  private ws: WebSocket | null = null;
  private config: Required<WebSocketConfig>;
  private handlers = new Map<MessageType, Set<MessageHandler>>();
  private retryCount = 0;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private heartbeatInterval: NodeJS.Timeout | null = null;

  constructor(config: WebSocketConfig) {
    this.config = {
      reconnect: true,
      maxRetries: 5,
      retryDelay: 1000,
      ...config,
    };
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.config.url);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.retryCount = 0;
          this.startHeartbeat();
          resolve();
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event.data);
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('WebSocket closed');
          this.stopHeartbeat();
          if (this.config.reconnect) {
            this.scheduleReconnect();
          }
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  disconnect(): void {
    this.config.reconnect = false;
    this.stopHeartbeat();
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(type: MessageType, payload: any): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket is not connected');
    }

    const message: WebSocketMessage = {
      type,
      payload,
      timestamp: Date.now(),
    };

    this.ws.send(JSON.stringify(message));
  }

  subscribe(type: MessageType, handler: MessageHandler): () => void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set());
    }
    this.handlers.get(type)!.add(handler);

    // Return unsubscribe function
    return () => {
      this.handlers.get(type)?.delete(handler);
    };
  }

  private handleMessage(data: string): void {
    try {
      const message: WebSocketMessage = JSON.parse(data);
      const handlers = this.handlers.get(message.type);

      if (handlers) {
        handlers.forEach(handler => handler(message));
      }
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }

  private scheduleReconnect(): void {
    if (this.retryCount >= this.config.maxRetries) {
      console.error('Max reconnection attempts reached');
      return;
    }

    const delay = this.config.retryDelay * Math.pow(2, this.retryCount);
    this.retryCount++;

    console.log(`Reconnecting in ${delay}ms (attempt ${this.retryCount}/${this.config.maxRetries})`);

    this.reconnectTimeout = setTimeout(() => {
      this.connect().catch(error => {
        console.error('Reconnection failed:', error);
      });
    }, delay);
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000); // 30 seconds
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }
}
```

#### Step 4: Integrate with Store
**File:** `src/store/diagnosisStore.ts`

```typescript
import { create } from 'zustand';
import { WebSocketManager } from '@/lib/websocket/manager';

interface DiagnosisStore {
  wsManager: WebSocketManager | null;
  initializeWebSocket: () => void;
  disconnectWebSocket: () => void;
}

export const useDiagnosisStore = create<DiagnosisStore>((set, get) => ({
  wsManager: null,

  initializeWebSocket: () => {
    const wsManager = new WebSocketManager({
      url: 'ws://localhost:8000/api/v1/agent/ws',
    });

    wsManager.subscribe('agent_message', (message) => {
      // Handle agent message
      console.log('Agent message:', message.payload);
    });

    wsManager.subscribe('error', (message) => {
      // Handle error
      console.error('WebSocket error:', message.payload);
    });

    wsManager.connect();
    set({ wsManager });
  },

  disconnectWebSocket: () => {
    const { wsManager } = get();
    wsManager?.disconnect();
    set({ wsManager: null });
  },
}));
```

---

## Guide 3: Implementing State Persistence

### Overview
Add automatic state persistence to localStorage with selective saving.

### Step-by-Step Implementation

#### Step 1: Create Persistence Utility
**File:** `src/lib/storage/persistence.ts`

```typescript
export interface PersistenceConfig<T> {
  key: string;
  storage?: Storage;
  serialize?: (state: T) => string;
  deserialize?: (str: string) => T;
  partialize?: (state: T) => Partial<T>;
}

export function createPersistence<T>(config: PersistenceConfig<T>) {
  const {
    key,
    storage = localStorage,
    serialize = JSON.stringify,
    deserialize = JSON.parse,
    partialize = (state) => state,
  } = config;

  return {
    getItem: (): T | null => {
      try {
        const item = storage.getItem(key);
        return item ? deserialize(item) : null;
      } catch (error) {
        console.error('Failed to load persisted state:', error);
        return null;
      }
    },

    setItem: (state: T): void => {
      try {
        const partialState = partialize(state);
        storage.setItem(key, serialize(partialState as T));
      } catch (error) {
        console.error('Failed to persist state:', error);
      }
    },

    removeItem: (): void => {
      storage.removeItem(key);
    },
  };
}
```

#### Step 2: Create Zustand Middleware
**File:** `src/lib/storage/middleware.ts`

```typescript
import { StateCreator, StoreMutatorIdentifier } from 'zustand';
import { createPersistence, PersistenceConfig } from './persistence';

export interface PersistOptions<T> extends Omit<PersistenceConfig<T>, 'key'> {
  name: string;
}

export const persist = <
  T,
  Mps extends [StoreMutatorIdentifier, unknown][] = [],
  Mcs extends [StoreMutatorIdentifier, unknown][] = []
>(
  config: StateCreator<T, Mps, Mcs>,
  options: PersistOptions<T>
) => {
  return (set: any, get: any, api: any) => {
    const persistence = createPersistence<T>({
      key: options.name,
      ...options,
    });

    // Hydrate state on initialization
    const persistedState = persistence.getItem();
    if (persistedState) {
      api.setState(persistedState, true);
    }

    // Wrap setState to persist on every change
    const originalSetState = api.setState;
    api.setState = (partial: any, replace?: boolean) => {
      originalSetState(partial, replace);
      persistence.setItem(api.getState());
    };

    return config(set, get, api);
  };
};
```

#### Step 3: Apply to Store
**File:** `src/store/authStore.ts`

```typescript
import { create } from 'zustand';
import { persist } from '@/lib/storage/middleware';

interface AuthStore {
  user: User | null;
  token: string | null;
  login: (user: User, token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      user: null,
      token: null,

      login: (user, token) => {
        set({ user, token });
      },

      logout: () => {
        set({ user: null, token: null });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
      }),
    }
  )
);
```

---

## Guide 4: Implementing Service Layer

### Overview
Extract business logic from components into reusable service classes.

### Step-by-Step Implementation

#### Step 1: Create Service Structure
```bash
mkdir -p src/services
touch src/services/diagnosisService.ts
touch src/services/knowledgeService.ts
```

#### Step 2: Define Service Interface
**File:** `src/services/diagnosisService.ts`

```typescript
import { api } from '@/lib/api';
import { Investigation, Evidence } from '@/types';

export class DiagnosisService {
  async startDiagnosis(caseId: string, description: string): Promise<Investigation> {
    const response = await api.post('/investigation/start', {
      case_id: caseId,
      description,
    });
    return response.data;
  }

  async stopDiagnosis(sessionId: string): Promise<void> {
    await api.post('/investigation/stop', { session_id: sessionId });
  }

  async approveAction(sessionId: string, actionId: string): Promise<void> {
    await api.post('/investigation/approve-action', {
      session_id: sessionId,
      action_id: actionId,
    });
  }

  async rejectAction(sessionId: string, actionId: string, reason: string): Promise<void> {
    await api.post('/investigation/reject-action', {
      session_id: sessionId,
      action_id: actionId,
      reason,
    });
  }

  async getEvidence(sessionId: string): Promise<Evidence[]> {
    const response = await api.get(`/investigation/${sessionId}/evidence`);
    return response.data;
  }
}

export const diagnosisService = new DiagnosisService();
```

#### Step 3: Use Service in Store
**File:** `src/store/diagnosisStore.ts`

```typescript
import { create } from 'zustand';
import { diagnosisService } from '@/services/diagnosisService';

interface DiagnosisStore {
  startDiagnosis: (caseId: string, description: string) => Promise<void>;
  stopDiagnosis: () => Promise<void>;
}

export const useDiagnosisStore = create<DiagnosisStore>((set, get) => ({
  startDiagnosis: async (caseId, description) => {
    try {
      const investigation = await diagnosisService.startDiagnosis(caseId, description);
      set({ currentInvestigation: investigation });
    } catch (error) {
      console.error('Failed to start diagnosis:', error);
      throw error;
    }
  },

  stopDiagnosis: async () => {
    const { currentInvestigation } = get();
    if (!currentInvestigation) return;

    try {
      await diagnosisService.stopDiagnosis(currentInvestigation.session_id);
      set({ currentInvestigation: null });
    } catch (error) {
      console.error('Failed to stop diagnosis:', error);
      throw error;
    }
  },
}));
```

#### Step 4: Use in Components
**File:** `src/components/investigation/DiagnosisControl.tsx`

```typescript
import { useDiagnosisStore } from '@/store/diagnosisStore';

export function DiagnosisControl() {
  const { startDiagnosis, stopDiagnosis } = useDiagnosisStore();

  const handleStart = async () => {
    await startDiagnosis('case-123', 'System is slow');
  };

  return (
    <button onClick={handleStart}>Start Diagnosis</button>
  );
}
```
