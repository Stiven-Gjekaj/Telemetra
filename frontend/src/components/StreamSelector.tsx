import { useEffect, useState } from 'react';
import { StreamInfo } from '../types';
import { ApiService } from '../services/api';
import './StreamSelector.css';

interface StreamSelectorProps {
  selectedStreamId: string | null;
  onSelectStream: (streamId: string) => void;
}

function StreamSelector({ selectedStreamId, onSelectStream }: StreamSelectorProps) {
  const [streams, setStreams] = useState<StreamInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStreams();
    // Refresh streams every 30 seconds
    const interval = setInterval(loadStreams, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadStreams = async () => {
    try {
      setError(null);
      const data = await ApiService.getStreams();
      setStreams(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load streams');
      console.error('Error loading streams:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="stream-selector loading">Loading streams...</div>;
  }

  if (error) {
    return (
      <div className="stream-selector error">
        <p>Error: {error}</p>
        <button onClick={loadStreams}>Retry</button>
      </div>
    );
  }

  return (
    <div className="stream-selector">
      <h2>Active Streams</h2>
      <div className="stream-list">
        {streams.length === 0 ? (
          <p className="no-streams">No active streams found</p>
        ) : (
          streams.map((stream) => (
            <div
              key={stream.stream_id}
              className={`stream-card ${selectedStreamId === stream.stream_id ? 'selected' : ''}`}
              onClick={() => onSelectStream(stream.stream_id)}
            >
              <div className="stream-header">
                <span className="channel-name">{stream.channel_name}</span>
                {stream.is_live && <span className="live-badge">LIVE</span>}
              </div>
              {stream.title && <p className="stream-title">{stream.title}</p>}
              <div className="stream-stats">
                <span>👁️ {stream.total_viewers.toLocaleString()}</span>
                <span>📈 Peak: {stream.peak_viewers.toLocaleString()}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default StreamSelector;
