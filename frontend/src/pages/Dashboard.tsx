import React, { useEffect, useState } from 'react';
import PulseBar from '../components/PulseBar';
import ChatRateChart from '../components/ChatRateChart';
import './Dashboard.css';

interface StreamMetrics {
  stream_id: string;
  chat?: {
    window_start: string;
    message_count: number;
    unique_chatters: number;
  };
  viewers?: {
    timestamp: string;
    viewer_count: number;
  };
  timestamp: string;
}

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

const Dashboard: React.FC = () => {
  const [streams, setStreams] = useState<any[]>([]);
  const [selectedStreamId, setSelectedStreamId] = useState<string>('');
  const [liveMetrics, setLiveMetrics] = useState<StreamMetrics | null>(null);
  const [chatHistory, setChatHistory] = useState<any[]>([]);
  const [viewerHistory, setViewerHistory] = useState<any[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  const [ws, setWs] = useState<WebSocket | null>(null);

  // Fetch available streams
  useEffect(() => {
    const fetchStreams = async () => {
      try {
        const response = await fetch(`${API_URL}/streams?status=live`);
        const data = await response.json();
        setStreams(data.streams);

        // Auto-select first stream
        if (data.streams.length > 0 && !selectedStreamId) {
          setSelectedStreamId(data.streams[0].stream_id);
        }
      } catch (error) {
        console.error('Error fetching streams:', error);
      }
    };

    fetchStreams();
    const interval = setInterval(fetchStreams, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [selectedStreamId]);

  // Fetch historical metrics
  useEffect(() => {
    if (!selectedStreamId) return;

    const fetchMetrics = async () => {
      try {
        const response = await fetch(`${API_URL}/streams/${selectedStreamId}/metrics?minutes=30`);
        const data = await response.json();

        setChatHistory(data.chat_metrics || []);
        setViewerHistory(data.viewer_metrics || []);
      } catch (error) {
        console.error('Error fetching metrics:', error);
      }
    };

    fetchMetrics();
  }, [selectedStreamId]);

  // WebSocket connection for live updates
  useEffect(() => {
    if (!selectedStreamId) return;

    const connectWebSocket = () => {
      setConnectionStatus('connecting');
      const websocket = new WebSocket(`${WS_URL}/live/${selectedStreamId}`);

      websocket.onopen = () => {
        console.log('WebSocket connected');
        setConnectionStatus('connected');
      };

      websocket.onmessage = (event) => {
        const data: StreamMetrics = JSON.parse(event.data);
        setLiveMetrics(data);

        // Update history
        if (data.chat) {
          setChatHistory(prev => [data.chat!, ...prev].slice(0, 30));
        }
        if (data.viewers) {
          setViewerHistory(prev => [data.viewers!, ...prev].slice(0, 30));
        }
      };

      websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('disconnected');
      };

      websocket.onclose = () => {
        console.log('WebSocket disconnected');
        setConnectionStatus('disconnected');

        // Reconnect after 5 seconds
        setTimeout(connectWebSocket, 5000);
      };

      setWs(websocket);
    };

    connectWebSocket();

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [selectedStreamId]);

  // Fallback to polling if WebSocket is not connected
  useEffect(() => {
    if (connectionStatus === 'connected' || !selectedStreamId) return;

    const pollMetrics = async () => {
      try {
        const response = await fetch(`${API_URL}/streams/${selectedStreamId}/metrics?minutes=1`);
        const data = await response.json();

        if (data.chat_metrics.length > 0) {
          const latest = data.chat_metrics[0];
          setLiveMetrics({
            stream_id: selectedStreamId,
            chat: latest,
            viewers: data.viewer_metrics[0],
            timestamp: new Date().toISOString()
          });
        }
      } catch (error) {
        console.error('Error polling metrics:', error);
      }
    };

    const interval = setInterval(pollMetrics, 5000);
    return () => clearInterval(interval);
  }, [connectionStatus, selectedStreamId]);

  const currentViewerCount = liveMetrics?.viewers?.viewer_count ||
                            (viewerHistory.length > 0 ? viewerHistory[0].viewer_count : 0);

  const currentChatRate = liveMetrics?.chat?.message_count ||
                         (chatHistory.length > 0 ? chatHistory[0].message_count : 0);

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>📊 Telemetra</h1>
        <p className="subtitle">Real-time Twitch Analytics</p>

        <div className="stream-selector">
          <label>Select Stream: </label>
          <select
            value={selectedStreamId}
            onChange={(e) => setSelectedStreamId(e.target.value)}
          >
            {streams.map(stream => (
              <option key={stream.stream_id} value={stream.stream_id}>
                {stream.channel_name} - {stream.stream_id}
              </option>
            ))}
          </select>

          <span className={`connection-status ${connectionStatus}`}>
            {connectionStatus === 'connected' && '🟢 Live'}
            {connectionStatus === 'connecting' && '🟡 Connecting...'}
            {connectionStatus === 'disconnected' && '🔴 Polling'}
          </span>
        </div>
      </header>

      <div className="metrics-grid">
        <div className="metric-card">
          <h3>Viewer Count</h3>
          <PulseBar
            value={currentViewerCount}
            max={2000}
            label="viewers"
            color="#9146FF"
          />
        </div>

        <div className="metric-card">
          <h3>Chat Rate</h3>
          <PulseBar
            value={currentChatRate}
            max={100}
            label="msgs/min"
            color="#00F2EA"
          />
        </div>

        <div className="metric-card large">
          <h3>Chat Activity (Last 30 Minutes)</h3>
          <ChatRateChart data={chatHistory} />
        </div>

        <div className="metric-card">
          <h3>Live Stats</h3>
          <div className="stats-list">
            <div className="stat-item">
              <span className="stat-label">Unique Chatters:</span>
              <span className="stat-value">
                {liveMetrics?.chat?.unique_chatters || chatHistory[0]?.unique_chatters || 0}
              </span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Messages/Min:</span>
              <span className="stat-value">{currentChatRate}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Viewers:</span>
              <span className="stat-value">{currentViewerCount}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Last Update:</span>
              <span className="stat-value">
                {liveMetrics ? new Date(liveMetrics.timestamp).toLocaleTimeString() : 'N/A'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
