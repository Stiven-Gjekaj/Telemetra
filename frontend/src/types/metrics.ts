/**
 * Core metric types for Telemetra streaming analytics
 */

/**
 * WebSocket connection states
 */
export enum ConnectionState {
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  ERROR = 'error',
}

/**
 * Emote data structure with frequency information
 */
export interface Emote {
  /** Emote name or identifier */
  name: string;
  /** Number of times emote was used */
  count: number;
  /** Optional emote URL for rendering */
  url?: string;
}

/**
 * Moment/Anomaly detection result
 */
export interface Moment {
  /** Unique identifier for the moment */
  id: string;
  /** Timestamp when the moment occurred */
  timestamp: number;
  /** Type of moment detected */
  type: 'chat_spike' | 'viewer_spike' | 'sentiment_shift' | 'custom';
  /** Description of what was detected */
  description: string;
  /** Severity level (0-1) */
  severity: number;
  /** Optional metadata */
  metadata?: Record<string, unknown>;
}

/**
 * Time-series data point for charts
 */
export interface TimeSeriesDataPoint {
  /** Unix timestamp in milliseconds */
  timestamp: number;
  /** Metric value */
  value: number;
  /** Optional label */
  label?: string;
}

/**
 * Chat rate metrics over time
 */
export interface ChatRateMetrics {
  /** Array of time-series data points */
  data: TimeSeriesDataPoint[];
  /** Current messages per minute */
  currentRate: number;
  /** Average rate over the window */
  averageRate: number;
  /** Peak rate observed */
  peakRate: number;
}

/**
 * Viewer count metrics
 */
export interface ViewerMetrics {
  /** Current viewer count */
  current: number;
  /** Peak viewer count */
  peak: number;
  /** Average viewer count */
  average: number;
  /** Historical data points */
  history: TimeSeriesDataPoint[];
}

/**
 * Sentiment analysis result
 */
export interface SentimentMetrics {
  /** Overall sentiment score (-1 to 1) */
  score: number;
  /** Positive message percentage */
  positive: number;
  /** Negative message percentage */
  negative: number;
  /** Neutral message percentage */
  neutral: number;
}

/**
 * Aggregated stream metrics
 */
export interface StreamMetrics {
  /** Stream identifier */
  streamId: string;
  /** Last update timestamp */
  timestamp: number;
  /** Viewer metrics */
  viewers: ViewerMetrics;
  /** Chat rate information */
  chatRate: ChatRateMetrics;
  /** Top emotes */
  topEmotes: Emote[];
  /** Sentiment analysis */
  sentiment?: SentimentMetrics;
  /** Recent moments/anomalies */
  moments: Moment[];
}

/**
 * WebSocket message envelope
 */
export interface WebSocketMessage<T = unknown> {
  /** Message type identifier */
  type: 'metrics' | 'moment' | 'error' | 'ping' | 'pong';
  /** Message payload */
  data: T;
  /** Message timestamp */
  timestamp: number;
}

/**
 * Metrics update message payload
 */
export interface MetricsUpdatePayload {
  /** Viewer count update */
  viewer_count?: number;
  /** Chat messages per minute */
  chat_rate?: number;
  /** Top emotes list */
  top_emotes?: Array<{ name: string; count: number }>;
  /** Average sentiment score */
  sentiment_score?: number;
  /** Timestamp of the metrics */
  timestamp: number;
}

/**
 * Moment detection message payload
 */
export interface MomentDetectedPayload {
  /** Moment identifier */
  id: string;
  /** Moment type */
  type: string;
  /** Description */
  description: string;
  /** Severity (0-1) */
  severity: number;
  /** Detection timestamp */
  timestamp: number;
  /** Additional metadata */
  metadata?: Record<string, unknown>;
}

/**
 * Error message payload
 */
export interface ErrorPayload {
  /** Error code */
  code: string;
  /** Error message */
  message: string;
  /** Additional error details */
  details?: Record<string, unknown>;
}

/**
 * WebSocket hook configuration
 */
export interface WebSocketConfig {
  /** WebSocket URL to connect to */
  url: string;
  /** Auto-reconnect on disconnect */
  autoReconnect?: boolean;
  /** Reconnect interval in milliseconds */
  reconnectInterval?: number;
  /** Maximum reconnection attempts (0 = infinite) */
  maxReconnectAttempts?: number;
  /** Heartbeat interval in milliseconds */
  heartbeatInterval?: number;
  /** Connection timeout in milliseconds */
  connectionTimeout?: number;
}

/**
 * WebSocket hook return type
 */
export interface UseWebSocketReturn {
  /** Current connection state */
  state: ConnectionState;
  /** Latest metrics data */
  metrics: StreamMetrics | null;
  /** Error information if any */
  error: string | null;
  /** Manually reconnect */
  reconnect: () => void;
  /** Manually disconnect */
  disconnect: () => void;
  /** Send message to server */
  send: (message: unknown) => void;
}

/**
 * Chart configuration options
 */
export interface ChartConfig {
  /** Chart width */
  width?: number;
  /** Chart height */
  height?: number;
  /** Color scheme */
  colors?: string[];
  /** Show grid lines */
  showGrid?: boolean;
  /** Show tooltip */
  showTooltip?: boolean;
  /** Animation duration */
  animationDuration?: number;
}
