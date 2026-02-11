import { DiagnosisEvent, parseDiagnosisEvent } from '../contracts/diagnosisProtocol';

export type WSMessage = DiagnosisEvent;

export type OutboundMessageType =
  | 'start_diagnosis'
  | 'stop_diagnosis'
  | 'approve_action'
  | 'reject_action'
  | 'pause_diagnosis'
  | 'resume_diagnosis'
  | 'confirmation_response';

export interface JSONRPCRequest<TData extends Record<string, unknown>> {
  type: OutboundMessageType;
  data?: TData;
  timestamp?: string;
}

export interface AgentMessage {
  id: string;
  agent: string;
  timestamp: string;
  content: string;
  type: 'info' | 'hypothesis' | 'action' | 'evidence' | 'decision' | 'error';
}

export interface ActionProposal {
  id: string;
  title: string;
  description: string;
  confidence: number;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  requiresConfirmation: boolean;
  canBeInterrupted: boolean;
}

export interface DiagnosisStatus {
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'interrupted';
  progress: number;
  currentStep?: string;
}

export interface ConfirmationRequired {
  id: string;
  actionId: string;
  message: string;
  description?: string;
  options?: Array<{ label: string; value: string }>;
  defaultOption?: string;
  riskLevel?: 'R0' | 'R1' | 'R2' | 'R3';
  impactScope?: string;
  rollbackPlan?: string;
  approverRoles?: string[];
  timeout?: number;
  timeoutSeconds?: number;
  timeoutStrategy?: string;
  requiresSecondConfirmation?: boolean;
}

export type MessageHandler = (message: DiagnosisEvent) => void;
export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000;
  private messageHandlers: Set<MessageHandler> = new Set();
  private connectionStatus: ConnectionStatus = 'disconnected';
  private statusHandlers: Set<(status: ConnectionStatus) => void> = new Set();
  private reconnectTimer: NodeJS.Timeout | null = null;
  private manualDisconnect = false;
  private connectingPromise: Promise<void> | null = null;

  constructor(url: string = 'ws://localhost:8000/api/v1/agent/ws') {
    this.url = url;
  }

  connect(): Promise<void> {
    if (this.ws?.readyState === WebSocket.OPEN) return Promise.resolve();
    if (this.ws?.readyState === WebSocket.CONNECTING && this.connectingPromise) return this.connectingPromise;

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.manualDisconnect = false;
    this.connectingPromise = new Promise((resolve, reject) => {
      try {
        this.setConnectionStatus('connecting');
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          this.reconnectAttempts = 0;
          this.setConnectionStatus('connected');
          this.connectingPromise = null;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const raw = JSON.parse(event.data) as unknown;
            const message = parseDiagnosisEvent(raw);
            if (!message) {
              console.warn('[WebSocket] Dropped message not matching diagnosis protocol');
              return;
            }
            this.notifyHandlers(message);
          } catch (error) {
            console.error('[WebSocket] Failed to parse message:', error);
          }
        };

        this.ws.onerror = (error) => {
          this.setConnectionStatus('error');
          this.connectingPromise = null;
          reject(error);
        };

        this.ws.onclose = () => {
          this.setConnectionStatus('disconnected');
          this.connectingPromise = null;
          this.attemptReconnect();
        };
      } catch (error) {
        this.setConnectionStatus('error');
        this.connectingPromise = null;
        reject(error);
      }
    });

    return this.connectingPromise;
  }

  disconnect(): void {
    this.manualDisconnect = true;
    this.reconnectAttempts = 0;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.reconnectTimer = null;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.connectingPromise = null;
    this.setConnectionStatus('disconnected');
  }

  private attemptReconnect(): void {
    if (this.manualDisconnect || this.reconnectAttempts >= this.maxReconnectAttempts) return;

    this.reconnectAttempts += 1;
    const delay = this.reconnectDelay * this.reconnectAttempts;
    this.reconnectTimer = setTimeout(() => {
      this.connect().catch((error) => {
        console.error('[WebSocket] Reconnection failed:', error);
      });
    }, delay);
  }

  send(type: OutboundMessageType | string, data: Record<string, unknown>): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;

    const safeType = type as OutboundMessageType;
    const request: JSONRPCRequest<Record<string, unknown>> = {
      type: safeType,
      data,
      timestamp: new Date().toISOString(),
    };
    this.ws.send(JSON.stringify(request));
  }

  startDiagnosis(symptom: string, description: string, agentType = 'diagnosis', context?: Record<string, unknown>, mode = 'auto'): void {
    this.send('start_diagnosis', { agent_type: agentType, symptom, description, context, mode });
  }

  stopDiagnosis(reason?: string): void {
    this.send('stop_diagnosis', { reason });
  }

  approveAction(actionId: string): void {
    this.send('approve_action', { actionId });
  }

  rejectAction(actionId: string, reason?: string): void {
    this.send('reject_action', { actionId, reason });
  }

  pauseDiagnosis(): void {
    this.send('pause_diagnosis', {});
  }

  resumeDiagnosis(): void {
    this.send('resume_diagnosis', {});
  }

  respondToConfirmation(confirmationId: string, response: Record<string, unknown>): void {
    this.send('confirmation_response', { confirmationId, response });
  }

  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler);
    return () => this.messageHandlers.delete(handler);
  }

  onConnectionStatus(handler: (status: ConnectionStatus) => void): () => void {
    this.statusHandlers.add(handler);
    return () => this.statusHandlers.delete(handler);
  }

  private notifyHandlers(message: DiagnosisEvent): void {
    this.messageHandlers.forEach((handler) => {
      try {
        handler(message);
      } catch (error) {
        console.error('[WebSocket] Handler error:', error);
      }
    });
  }

  private setConnectionStatus(status: ConnectionStatus): void {
    this.connectionStatus = status;
    this.statusHandlers.forEach((handler) => {
      try {
        handler(status);
      } catch (error) {
        console.error('[WebSocket] Status handler error:', error);
      }
    });
  }

  getConnectionStatus(): ConnectionStatus {
    return this.connectionStatus;
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export const wsService = new WebSocketService();
