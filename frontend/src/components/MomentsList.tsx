import { Moment } from '../types';
import './MomentsList.css';

interface MomentsListProps {
  moments: Moment[];
}

function MomentsList({ moments }: MomentsListProps) {
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  const getSeverityClass = (severity: number) => {
    if (severity >= 0.8) return 'high';
    if (severity >= 0.5) return 'medium';
    return 'low';
  };

  if (moments.length === 0) {
    return (
      <div className="moments-list empty">
        <p>No notable moments detected yet</p>
      </div>
    );
  }

  return (
    <div className="moments-list">
      {moments.map((moment, index) => (
        <div
          key={`${moment.stream_id}-${moment.timestamp}-${index}`}
          className={`moment-item severity-${getSeverityClass(moment.severity)}`}
        >
          <div className="moment-header">
            <span className="moment-type">{moment.moment_type}</span>
            <span className="moment-timestamp">{formatTimestamp(moment.timestamp)}</span>
          </div>
          {moment.description && (
            <div className="moment-description">{moment.description}</div>
          )}
          <div className="moment-severity">
            Severity: <span className="severity-value">{(moment.severity * 100).toFixed(0)}%</span>
          </div>
        </div>
      ))}
    </div>
  );
}

export default MomentsList;
