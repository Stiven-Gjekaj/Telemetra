import { useEffect, useRef, useState, useCallback } from 'react';
import type {
  ConnectionState,
  WebSocketConfig,
  UseWebSocketReturn,
  StreamMetrics,
  WebSocketMessage,
  MetricsUpdatePayload,
  MomentDetectedPayload,
  Moment,
  TimeSeriesDataPoint,
  Emote,
} from '../types/metrics';

/**
 * Default configuration values
 */
const DEFAULT_CONFIG: Required<Omit<WebSocketConfig, 'url'>> = {
  autoReconnect: true,
  reconnectInterval: 3000,
  maxReconnectAttempts: 10,
  heartbeatInterval: 30000,
  connectionTimeout: 10000,
};

/**
 * Maximum number of data points to keep in memory for time-series data
 */
const MAX_HISTORY_POINTS = 100;

/**
 * Custom hook for managing WebSocket connections with auto-reconnect
 * and state management for streaming analytics data.
 *
 * @param config - WebSocket configuration options
 * @returns WebSocket state and control functions
 *
 * @example
 * ```tsx
 * const { state, metrics, error, reconnect } = useWebSocket({
 *   url: 'ws://localhost:8000/live/demo_stream',
 *   autoReconnect: true,
 * });
 * ```
 */
export function useWebSocket(config: WebSocketConfig): UseWebSocketReturn {
  const mergedConfig = { ...DEFAULT_CONFIG, ...config };

  // Connection state
  const [state, setState] = useState<ConnectionState>(ConnectionState.DISCONNECTED);
  const [error, setError] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<StreamMetrics | null>(null);

  // Refs for managing connection lifecycle
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const isManualDisconnect = useRef(false);

  /**
   * Initialize default metrics structure
   */
  const initializeMetrics = useCallback((): StreamMetrics => {
    const now = Date.now();
    return {
      streamId: config.url.split('/').pop() || 'unknown',
      timestamp: now,
      viewers: {
        current: 0,
        peak: 0,
        average: 0,
        history: [],
      },
      chatRate: {
        data: [],
        currentRate: 0,
        averageRate: 0,
        peakRate: 0,
      },
      topEmotes: [],
      moments: [],
    };
  }, [config.url]);

  /**
   * Update metrics with new data point, maintaining history limit
   */
  const updateMetrics = useCallback((
    payload: MetricsUpdatePayload,
    currentMetrics: StreamMetrics
  ): StreamMetrics => {
    const now = payload.timestamp || Date.now();

    // Update viewer metrics
    const newViewerCount = payload.viewer_count ?? currentMetrics.viewers.current;
    const viewerHistory = [
      ...currentMetrics.viewers.history,
      { timestamp: now, value: newViewerCount },
    ].slice(-MAX_HISTORY_POINTS);

    const viewerPeak = Math.max(currentMetrics.viewers.peak, newViewerCount);
    const viewerAverage = viewerHistory.length > 0
      ? viewerHistory.reduce((sum, pt) => sum + pt.value, 0) / viewerHistory.length
      : newViewerCount;

    // Update chat rate metrics
    const newChatRate = payload.chat_rate ?? currentMetrics.chatRate.currentRate;
    const chatRateData = [
      ...currentMetrics.chatRate.data,
      { timestamp: now, value: newChatRate },
    ].slice(-MAX_HISTORY_POINTS);

    const chatRatePeak = Math.max(currentMetrics.chatRate.peakRate, newChatRate);
    const chatRateAverage = chatRateData.length > 0
      ? chatRateData.reduce((sum, pt) => sum + pt.value, 0) / chatRateData.length
      : newChatRate;

    // Update top emotes
    const topEmotes: Emote[] = payload.top_emotes
      ? payload.top_emotes.map(e => ({
          name: e.name,
          count: e.count,
        }))
      : currentMetrics.topEmotes;

    return {
      ...currentMetrics,
      timestamp: now,
      viewers: {
        current: newViewerCount,
        peak: viewerPeak,
        average: Math.round(viewerAverage),
        history: viewerHistory,
      },
      chatRate: {
        data: chatRateData,
        currentRate: newChatRate,
        averageRate: Math.round(chatRateAverage * 10) / 10,
        peakRate: chatRatePeak,
      },
      topEmotes,
      sentiment: payload.sentiment_score !== undefined
        ? {
            score: payload.sentiment_score,
            positive: Math.max(0, payload.sentiment_score) * 100,
            negative: Math.abs(Math.min(0, payload.sentiment_score)) * 100,
            neutral: (1 - Math.abs(payload.sentiment_score)) * 100,
          }
        : currentMetrics.sentiment,
    };
  }, []);

  /**
   * Add a new moment to the metrics
   */
  const addMoment = useCallback((
    payload: MomentDetectedPayload,
    currentMetrics: StreamMetrics
  ): StreamMetrics => {
    const newMoment: Moment = {
      id: payload.id,
      timestamp: payload.timestamp,
      type: payload.type as Moment['type'],
      description: payload.description,
      severity: payload.severity,
      metadata: payload.metadata,
    };

    // Keep only the latest 50 moments
    const moments = [newMoment, ...currentMetrics.moments].slice(0, 50);

    return {
      ...currentMetrics,
      moments,
    };
  }, []);

  /**
   * Handle incoming WebSocket messages
   */
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);

      switch (message.type) {
        case 'metrics':
          setMetrics(prev =>
            updateMetrics(message.data as MetricsUpdatePayload, prev || initializeMetrics())
          );
          break;

        case 'moment':
          setMetrics(prev =>
            prev ? addMoment(message.data as MomentDetectedPayload, prev) : prev
          );
          break;

        case 'error':
          setError((message.data as { message: string }).message);
          break;

        case 'ping':
          // Respond to ping with pong
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: 'pong', timestamp: Date.now() }));
          }
          break;

        case 'pong':
          // Server acknowledged our heartbeat
          break;

        default:
          console.warn('Unknown message type:', message.type);
      }
    } catch (err) {
      console.error('Failed to parse WebSocket message:', err);
      setError('Failed to parse server message');
    }
  }, [updateMetrics, addMoment, initializeMetrics]);

  /**
   * Start heartbeat interval to keep connection alive
   */
  const startHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
    }

    heartbeatIntervalRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));
      }
    }, mergedConfig.heartbeatInterval);
  }, [mergedConfig.heartbeatInterval]);

  /**
   * Stop heartbeat interval
   */
  const stopHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
  }, []);

  /**
   * Attempt to reconnect to the WebSocket
   */
  const attemptReconnect = useCallback(() => {
    if (isManualDisconnect.current) {
      return;
    }

    if (
      mergedConfig.maxReconnectAttempts > 0 &&
      reconnectAttempts.current >= mergedConfig.maxReconnectAttempts
    ) {
      setError('Maximum reconnection attempts reached');
      setState(ConnectionState.ERROR);
      return;
    }

    reconnectAttempts.current += 1;
    setState(ConnectionState.CONNECTING);

    reconnectTimeoutRef.current = setTimeout(() => {
      connect();
    }, mergedConfig.reconnectInterval);
  }, [mergedConfig.maxReconnectAttempts, mergedConfig.reconnectInterval]);

  /**
   * Connect to the WebSocket server
   */
  const connect = useCallback(() => {
    try {
      // Clean up existing connection
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }

      setState(ConnectionState.CONNECTING);
      setError(null);

      const ws = new WebSocket(mergedConfig.url);
      wsRef.current = ws;

      ws.onopen = () => {
        setState(ConnectionState.CONNECTED);
        reconnectAttempts.current = 0;
        setError(null);
        startHeartbeat();

        // Initialize metrics on connection
        setMetrics(initializeMetrics());
      };

      ws.onmessage = handleMessage;

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('WebSocket connection error');
        setState(ConnectionState.ERROR);
      };

      ws.onclose = (event) => {
        stopHeartbeat();

        if (!isManualDisconnect.current) {
          setState(ConnectionState.DISCONNECTED);

          if (mergedConfig.autoReconnect) {
            attemptReconnect();
          }
        } else {
          setState(ConnectionState.DISCONNECTED);
        }
      };
    } catch (err) {
      console.error('Failed to create WebSocket:', err);
      setError('Failed to create WebSocket connection');
      setState(ConnectionState.ERROR);
    }
  }, [mergedConfig, handleMessage, startHeartbeat, stopHeartbeat, attemptReconnect, initializeMetrics]);

  /**
   * Manually disconnect from WebSocket
   */
  const disconnect = useCallback(() => {
    isManualDisconnect.current = true;

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    stopHeartbeat();

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setState(ConnectionState.DISCONNECTED);
  }, [stopHeartbeat]);

  /**
   * Manually reconnect to WebSocket
   */
  const reconnect = useCallback(() => {
    isManualDisconnect.current = false;
    reconnectAttempts.current = 0;

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    connect();
  }, [connect]);

  /**
   * Send a message to the WebSocket server
   */
  const send = useCallback((message: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not open. Current state:', state);
    }
  }, [state]);

  /**
   * Initialize connection on mount and cleanup on unmount
   */
  useEffect(() => {
    isManualDisconnect.current = false;
    connect();

    return () => {
      isManualDisconnect.current = true;

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }

      stopHeartbeat();

      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect, stopHeartbeat]);

  return {
    state,
    metrics,
    error,
    reconnect,
    disconnect,
    send,
  };
}
