import React from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { PulseBar } from '../components/PulseBar';
import { ChatFlow } from '../components/ChatFlow';
import { EmoteCloud } from '../components/EmoteCloud';
import { MomentsTimeline } from '../components/MomentsTimeline';
import { ConnectionState } from '../types/metrics';

/**
 * Props for the Dashboard component
 */
interface DashboardProps {
  /** Stream ID to connect to */
  streamId?: string;
}

/**
 * Connection status badge component
 */
const ConnectionBadge: React.FC<{ state: ConnectionState; error: string | null }> = ({
  state,
  error,
}) => {
  const getStatusConfig = () => {
    switch (state) {
      case ConnectionState.CONNECTED:
        return {
          color: 'bg-green-500',
          text: 'Connected',
          textColor: 'text-green-500',
          icon: '●',
        };
      case ConnectionState.CONNECTING:
        return {
          color: 'bg-yellow-500',
          text: 'Connecting...',
          textColor: 'text-yellow-500',
          icon: '◐',
        };
      case ConnectionState.DISCONNECTED:
        return {
          color: 'bg-gray-500',
          text: 'Disconnected',
          textColor: 'text-gray-500',
          icon: '○',
        };
      case ConnectionState.ERROR:
        return {
          color: 'bg-red-500',
          text: 'Error',
          textColor: 'text-red-500',
          icon: '✕',
        };
      default:
        return {
          color: 'bg-gray-500',
          text: 'Unknown',
          textColor: 'text-gray-500',
          icon: '?',
        };
    }
  };

  const config = getStatusConfig();

  return (
    <div className="flex items-center space-x-2">
      <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-dark-100 border border-dark-200">
        <div
          className={`w-2 h-2 rounded-full ${config.color} ${
            state === ConnectionState.CONNECTED ? 'animate-pulse' : ''
          }`}
        />
        <span className={`text-sm font-medium ${config.textColor}`}>{config.text}</span>
      </div>
      {error && (
        <div className="px-3 py-1.5 rounded-lg bg-red-500/10 border border-red-500">
          <span className="text-sm text-red-500">{error}</span>
        </div>
      )}
    </div>
  );
};

/**
 * Dashboard page component displaying real-time streaming analytics.
 * Connects to WebSocket and renders multiple visualization components.
 *
 * @param props - Component props
 * @returns React component
 */
export const Dashboard: React.FC<DashboardProps> = ({ streamId = 'demo_stream' }) => {
  // Get WebSocket URL from environment or use default
  const wsUrl =
    import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
  const wsEndpoint = `${wsUrl}/live/${streamId}`;

  // Connect to WebSocket
  const { state, metrics, error, reconnect } = useWebSocket({
    url: wsEndpoint,
    autoReconnect: true,
    reconnectInterval: parseInt(import.meta.env.VITE_WS_RECONNECT_INTERVAL || '3000'),
    maxReconnectAttempts: parseInt(import.meta.env.VITE_WS_MAX_RECONNECT_ATTEMPTS || '10'),
  });

  const isConnected = state === ConnectionState.CONNECTED;

  return (
    <div className="min-h-screen bg-dark-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <header className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-dark-900 mb-2">
                Telemetra Analytics Dashboard
              </h1>
              <p className="text-dark-600">
                Real-time streaming analytics for{' '}
                <span className="font-mono text-primary-500">{streamId}</span>
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <ConnectionBadge state={state} error={error} />
              {state === ConnectionState.DISCONNECTED || state === ConnectionState.ERROR ? (
                <button
                  onClick={reconnect}
                  className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors font-medium"
                >
                  Reconnect
                </button>
              ) : null}
            </div>
          </div>
        </header>

        {/* Loading state */}
        {!isConnected && !metrics && (
          <div className="flex flex-col items-center justify-center h-96 bg-dark-100 rounded-lg border border-dark-200">
            <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-primary-500 mb-4" />
            <p className="text-dark-600 text-lg">Connecting to stream...</p>
            <p className="text-dark-500 text-sm mt-2">{wsEndpoint}</p>
          </div>
        )}

        {/* Main content grid */}
        {metrics && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left column - Viewer metrics */}
            <div className="lg:col-span-1">
              <PulseBar metrics={metrics.viewers} className="h-full" />
            </div>

            {/* Middle column - Chat activity */}
            <div className="lg:col-span-2">
              <ChatFlow metrics={metrics.chatRate} height={350} />
            </div>

            {/* Full width - Emote cloud */}
            <div className="lg:col-span-3">
              <EmoteCloud emotes={metrics.topEmotes} height={400} maxEmotes={40} />
            </div>

            {/* Full width - Moments timeline */}
            <div className="lg:col-span-3">
              <MomentsTimeline moments={metrics.moments} maxMoments={15} />
            </div>
          </div>
        )}

        {/* Footer with metadata */}
        {metrics && (
          <footer className="mt-8 pt-6 border-t border-dark-200">
            <div className="flex items-center justify-between text-sm text-dark-500">
              <div className="flex items-center space-x-4">
                <span>
                  Last update:{' '}
                  {new Date(metrics.timestamp).toLocaleTimeString('en-US', {
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                  })}
                </span>
                {metrics.sentiment && (
                  <span>
                    Sentiment:{' '}
                    <span
                      className={
                        metrics.sentiment.score > 0
                          ? 'text-green-500'
                          : metrics.sentiment.score < 0
                          ? 'text-red-500'
                          : 'text-dark-600'
                      }
                    >
                      {metrics.sentiment.score > 0 ? '😊' : metrics.sentiment.score < 0 ? '😟' : '😐'}{' '}
                      {(metrics.sentiment.score * 100).toFixed(1)}%
                    </span>
                  </span>
                )}
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-xs text-dark-400">Powered by Telemetra</span>
              </div>
            </div>
          </footer>
        )}
      </div>
    </div>
  );
};
