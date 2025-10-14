import { StreamInfo, ChatMetrics, ViewerMetrics, Moment } from '../types';

const API_BASE = '/api';

export class ApiService {
  static async getStreams(): Promise<StreamInfo[]> {
    const response = await fetch(`${API_BASE}/streams`);
    if (!response.ok) {
      throw new Error(`Failed to fetch streams: ${response.statusText}`);
    }
    return response.json();
  }

  static async getStream(streamId: string): Promise<StreamInfo> {
    const response = await fetch(`${API_BASE}/streams/${streamId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch stream: ${response.statusText}`);
    }
    return response.json();
  }

  static async getChatMetrics(
    streamId: string,
    limit: number = 100
  ): Promise<ChatMetrics[]> {
    const response = await fetch(
      `${API_BASE}/streams/${streamId}/chat-metrics?limit=${limit}`
    );
    if (!response.ok) {
      throw new Error(`Failed to fetch chat metrics: ${response.statusText}`);
    }
    return response.json();
  }

  static async getViewerMetrics(
    streamId: string,
    limit: number = 100
  ): Promise<ViewerMetrics[]> {
    const response = await fetch(
      `${API_BASE}/streams/${streamId}/viewer-metrics?limit=${limit}`
    );
    if (!response.ok) {
      throw new Error(`Failed to fetch viewer metrics: ${response.statusText}`);
    }
    return response.json();
  }

  static async getMoments(
    streamId: string,
    limit: number = 50
  ): Promise<Moment[]> {
    const response = await fetch(
      `${API_BASE}/streams/${streamId}/moments?limit=${limit}`
    );
    if (!response.ok) {
      throw new Error(`Failed to fetch moments: ${response.statusText}`);
    }
    return response.json();
  }

  static async healthCheck(): Promise<{ status: string }> {
    const response = await fetch(`${API_BASE}/health`);
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }
    return response.json();
  }
}
