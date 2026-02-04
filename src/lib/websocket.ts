export interface JSONRPCRequest {
  type: string;
  data?: any;
  timestamp?: string;
}

export interface JSONRPCResponse {
  type: string;
  data?: any;
  timestamp: string;
}

export interface WSMessage {
  type: 'agent_message' | 'action_proposal' | 'diagnosis_status' | 'error' | 'confirmation_required' | 'action_result' | 'timeline_update' | 'confidence_update';
  data: any;
  timestamp: string;
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
  riskLevel?: 'low' | 'medium' | 'high' | 'critical';
  timeout?: number;
}

export type MessageHandler = (message: WSMessage) => void;
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

  constructor(url: string = 'ws://localhost:8000/api/v1/agent/ws') {
    this.url = url;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.setConnectionStatus('connecting');
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('[WebSocket] Connected to agent CLI');
          this.reconnectAttempts = 0;
          this.setConnectionStatus('connected');
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WSMessage = JSON.parse(event.data);
            this.notifyHandlers(message);
          } catch (error) {
            console.error('[WebSocket] Failed to parse message:', error);
          }
        };

        this.ws.onerror = (error) => {
          console.error('[WebSocket] Error:', error);
          this.setConnectionStatus('error');
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('[WebSocket] Connection closed');
          this.setConnectionStatus('disconnected');
          this.attemptReconnect();
        };
      } catch (error) {
        this.setConnectionStatus('error');
        reject(error);
      }
    });
  }

  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    this.setConnectionStatus('disconnected');
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('[WebSocket] Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * this.reconnectAttempts;

    console.log(`[WebSocket] Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    this.reconnectTimer = setTimeout(() => {
      this.connect().catch((error) => {
        console.error('[WebSocket] Reconnection failed:', error);
      });
    }, delay);
  }

  send(type: string, data: any): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error('[WebSocket] Cannot send message: connection not open');
      return;
    }

    const request: JSONRPCRequest = {
      type,
      data,
      timestamp: new Date().toISOString(),
    };

    this.ws.send(JSON.stringify(request));
  }

  startDiagnosis(symptom: string, description: string, agentType: string = 'diagnosis', context?: any): void {
    this.send('start_diagnosis', { agent_type: agentType, symptom, description, context });
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

  respondToConfirmation(confirmationId: string, response: any): void {
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

  private notifyHandlers(message: WSMessage): void {
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
