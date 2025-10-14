import { useEffect, useState, useCallback } from 'react';
import { ChatMetrics, ViewerMetrics, Moment, WebSocketMessage } from '../types';
import { ApiService } from '../services/api';
import { WebSocketService } from '../services/websocket';
import LiveMetrics from './LiveMetrics';
import ViewerChart from './charts/ViewerChart';
import ChatRateChart from './charts/ChatRateChart';
import MomentsList from './MomentsList';
import './Dashboard.css';

interface DashboardProps {
  streamId: string;
}

function Dashboard({ streamId }: DashboardProps) {
  const [chatMetrics, setChatMetrics] = useState<ChatMetrics[]>([]);
  const [viewerMetrics, setViewerMetrics] = useState<ViewerMetrics[]>([]);
  const [moments, setMoments] = useState<Moment[]>([]);
  const [loading, setLoading] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);
  const [wsService] = useState(() => new WebSocketService());

  // Load initial historical data
  useEffect(() => {
    loadHistoricalData();
  }, [streamId]);

  // Setup WebSocket connection
  useEffect(() => {
    wsService.connect(streamId);

    const unsubscribe = wsService.subscribe(handleWebSocketMessage);

    const connectionCheck = setInterval(() => {
      setWsConnected(wsService.isConnected());
    }, 1000);

    return () => {
      unsubscribe();
      wsService.disconnect();
      clearInterval(connectionCheck);
    };
  }, [streamId, wsService]);

  const loadHistoricalData = async () => {
    try {
      setLoading(true);
      const [chat, viewer, momentData] = await Promise.all([
        ApiService.getChatMetrics(streamId, 100),
        ApiService.getViewerMetrics(streamId, 100),
        ApiService.getMoments(streamId, 50)
      ]);

      setChatMetrics(chat);
      setViewerMetrics(viewer);
      setMoments(momentData);
    } catch (error) {
      console.error('Error loading historical data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    const { topic, data } = message;

    if (topic === 'telemetra.chat') {
      const chatData = data as ChatMetrics;
      setChatMetrics(prev => [...prev, chatData].slice(-100));
    } else if (topic === 'telemetra.viewer') {
      const viewerData = data as ViewerMetrics;
      setViewerMetrics(prev => [...prev, viewerData].slice(-100));
    } else if (topic.includes('moment') || topic.includes('anomaly')) {
      const momentData = data as Moment;
      setMoments(prev => [momentData, ...prev].slice(0, 50));
    }
  }, []);

  if (loading) {
    return (
      <div className="dashboard loading">
        <p>Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h2>Stream Analytics</h2>
        <div className="connection-status">
          <span className={`status-indicator ${wsConnected ? 'connected' : 'disconnected'}`} />
          <span>{wsConnected ? 'Live' : 'Disconnected'}</span>
        </div>
      </div>

      <LiveMetrics
        chatMetrics={chatMetrics}
        viewerMetrics={viewerMetrics}
      />

      <div className="charts-grid">
        <div className="chart-container">
          <h3>Viewer Count</h3>
          <ViewerChart data={viewerMetrics} moments={moments} />
        </div>

        <div className="chart-container">
          <h3>Chat Activity</h3>
          <ChatRateChart data={chatMetrics} moments={moments} />
        </div>
      </div>

      <div className="moments-container">
        <h3>Notable Moments & Anomalies</h3>
        <MomentsList moments={moments} />
      </div>
    </div>
  );
}

export default Dashboard;
