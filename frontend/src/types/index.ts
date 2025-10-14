export interface StreamInfo {
  stream_id: string;
  channel_name: string;
  title?: string;
  is_live: boolean;
  total_viewers: number;
  peak_viewers: number;
  started_at: string;
}

export interface ChatMetrics {
  stream_id: string;
  window_start: string;
  window_end: string;
  message_count: number;
  unique_chatters: number;
  avg_message_length?: number;
}

export interface ViewerMetrics {
  stream_id: string;
  timestamp: string;
  viewer_count: number;
  chatter_count?: number;
  subscriber_count?: number;
}

export interface Moment {
  stream_id: string;
  moment_type: string;
  timestamp: string;
  description?: string;
  severity: number;
  metadata?: Record<string, any>;
}

export interface WebSocketMessage {
  topic: string;
  data: ChatMetrics | ViewerMetrics | Moment;
  timestamp: number;
}
