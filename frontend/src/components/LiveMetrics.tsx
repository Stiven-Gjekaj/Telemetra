import { useMemo } from 'react';
import { ChatMetrics, ViewerMetrics } from '../types';
import './LiveMetrics.css';

interface LiveMetricsProps {
  chatMetrics: ChatMetrics[];
  viewerMetrics: ViewerMetrics[];
}

function LiveMetrics({ chatMetrics, viewerMetrics }: LiveMetricsProps) {
  const latestMetrics = useMemo(() => {
    const latestChat = chatMetrics[chatMetrics.length - 1];
    const latestViewer = viewerMetrics[viewerMetrics.length - 1];

    // Calculate chat rate trend
    let chatRateTrend = 0;
    if (chatMetrics.length >= 2) {
      const current = chatMetrics[chatMetrics.length - 1].message_count;
      const previous = chatMetrics[chatMetrics.length - 2].message_count;
      chatRateTrend = current - previous;
    }

    // Calculate viewer trend
    let viewerTrend = 0;
    if (viewerMetrics.length >= 2) {
      const current = viewerMetrics[viewerMetrics.length - 1].viewer_count;
      const previous = viewerMetrics[viewerMetrics.length - 2].viewer_count;
      viewerTrend = current - previous;
    }

    return {
      messageCount: latestChat?.message_count || 0,
      uniqueChatters: latestChat?.unique_chatters || 0,
      avgMessageLength: latestChat?.avg_message_length || 0,
      viewerCount: latestViewer?.viewer_count || 0,
      chatRateTrend,
      viewerTrend
    };
  }, [chatMetrics, viewerMetrics]);

  const formatTrend = (value: number) => {
    if (value === 0) return '';
    const arrow = value > 0 ? '↑' : '↓';
    return `${arrow} ${Math.abs(value)}`;
  };

  return (
    <div className="live-metrics">
      <div className="metric-card">
        <div className="metric-label">Current Viewers</div>
        <div className="metric-value">
          {latestMetrics.viewerCount.toLocaleString()}
        </div>
        {latestMetrics.viewerTrend !== 0 && (
          <div className={`metric-trend ${latestMetrics.viewerTrend > 0 ? 'positive' : 'negative'}`}>
            {formatTrend(latestMetrics.viewerTrend)}
          </div>
        )}
      </div>

      <div className="metric-card">
        <div className="metric-label">Messages/Min</div>
        <div className="metric-value">
          {latestMetrics.messageCount.toLocaleString()}
        </div>
        {latestMetrics.chatRateTrend !== 0 && (
          <div className={`metric-trend ${latestMetrics.chatRateTrend > 0 ? 'positive' : 'negative'}`}>
            {formatTrend(latestMetrics.chatRateTrend)}
          </div>
        )}
      </div>

      <div className="metric-card">
        <div className="metric-label">Active Chatters</div>
        <div className="metric-value">
          {latestMetrics.uniqueChatters.toLocaleString()}
        </div>
      </div>

      <div className="metric-card">
        <div className="metric-label">Avg Message Length</div>
        <div className="metric-value">
          {latestMetrics.avgMessageLength.toFixed(1)}
        </div>
      </div>
    </div>
  );
}

export default LiveMetrics;
