import { useEffect, useState, useCallback } from 'react';
import { wsService, WSMessage, ConnectionStatus } from '../lib/websocket';

interface UseWebSocketReturn {
  isConnected: boolean;
  connectionStatus: ConnectionStatus;
  sendMessage: (type: string, data: any) => void;
  disconnect: () => void;
}

export function useWebSocket(): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [messageHandlers] = useState<Set<(message: WSMessage) => void>>(new Set());

  useEffect(() => {
    const connect = async () => {
      try {
        await wsService.connect();
        console.log('[useWebSocket] Connected');
      } catch (error) {
        console.error('[useWebSocket] Connection failed:', error);
      }
    };

    connect();

    const unsubscribeStatus = wsService.onConnectionStatus((status) => {
      setConnectionStatus(status);
      setIsConnected(status === 'connected');
    });

    return () => {
      unsubscribeStatus();
      wsService.disconnect();
    };
  }, []);

  const sendMessage = useCallback((type: string, data: any) => {
    wsService.send(type, data);
  }, []);

  const disconnect = useCallback(() => {
    wsService.disconnect();
  }, []);

  return {
    isConnected,
    connectionStatus,
    sendMessage,
    disconnect,
  };
}
