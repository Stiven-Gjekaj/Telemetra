import React, { useState } from 'react';
import type { Moment } from '../types/metrics';

/**
 * Props for the MomentsTimeline component
 */
interface MomentsTimelineProps {
  /** Array of detected moments/anomalies */
  moments: Moment[];
  /** Optional CSS class name */
  className?: string;
  /** Maximum number of moments to display */
  maxMoments?: number;
}

/**
 * Get icon for moment type
 */
const getMomentIcon = (type: Moment['type']): string => {
  switch (type) {
    case 'chat_spike':
      return '💬';
    case 'viewer_spike':
      return '👥';
    case 'sentiment_shift':
      return '😮';
    case 'custom':
    default:
      return '⚡';
  }
};

/**
 * Get color class for moment type
 */
const getMomentColor = (type: Moment['type']): { bg: string; border: string; text: string } => {
  switch (type) {
    case 'chat_spike':
      return { bg: 'bg-blue-500/10', border: 'border-blue-500', text: 'text-blue-500' };
    case 'viewer_spike':
      return { bg: 'bg-green-500/10', border: 'border-green-500', text: 'text-green-500' };
    case 'sentiment_shift':
      return { bg: 'bg-yellow-500/10', border: 'border-yellow-500', text: 'text-yellow-500' };
    case 'custom':
    default:
      return { bg: 'bg-purple-500/10', border: 'border-purple-500', text: 'text-purple-500' };
  }
};

/**
 * Get severity indicator
 */
const getSeverityIndicator = (severity: number): { color: string; label: string } => {
  if (severity >= 0.8) {
    return { color: 'bg-red-500', label: 'Critical' };
  } else if (severity >= 0.6) {
    return { color: 'bg-orange-500', label: 'High' };
  } else if (severity >= 0.4) {
    return { color: 'bg-yellow-500', label: 'Medium' };
  } else {
    return { color: 'bg-green-500', label: 'Low' };
  }
};

/**
 * MomentsTimeline component displays a list of detected anomalies and moments
 * with timestamps and severity indicators.
 *
 * @param props - Component props
 * @returns React component
 */
export const MomentsTimeline: React.FC<MomentsTimelineProps> = ({
  moments,
  className = '',
  maxMoments = 10,
}) => {
  const [expandedMoment, setExpandedMoment] = useState<string | null>(null);
  const [filter, setFilter] = useState<Moment['type'] | 'all'>('all');

  /**
   * Format timestamp to relative time
   */
  const formatRelativeTime = (timestamp: number): string => {
    const now = Date.now();
    const diff = now - timestamp;

    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    if (seconds > 0) return `${seconds}s ago`;
    return 'Just now';
  };

  /**
   * Format timestamp to full date/time
   */
  const formatFullTime = (timestamp: number): string => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  /**
   * Toggle moment expansion
   */
  const toggleExpand = (momentId: string) => {
    setExpandedMoment(prev => (prev === momentId ? null : momentId));
  };

  /**
   * Filter moments by type
   */
  const filteredMoments =
    filter === 'all'
      ? moments
      : moments.filter(m => m.type === filter);

  const displayedMoments = filteredMoments.slice(0, maxMoments);

  /**
   * Get count for each moment type
   */
  const typeCounts = moments.reduce((acc, moment) => {
    acc[moment.type] = (acc[moment.type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className={`bg-dark-100 rounded-lg p-6 border border-dark-200 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-dark-800">Detected Moments</h3>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-dark-500">Total:</span>
          <span className="text-lg font-bold text-primary-500">{moments.length}</span>
        </div>
      </div>

      {/* Filter buttons */}
      <div className="flex flex-wrap gap-2 mb-4">
        <button
          onClick={() => setFilter('all')}
          className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
            filter === 'all'
              ? 'bg-primary-500 text-white'
              : 'bg-dark-200 text-dark-600 hover:bg-dark-300'
          }`}
        >
          All ({moments.length})
        </button>
        {(['chat_spike', 'viewer_spike', 'sentiment_shift', 'custom'] as const).map(type => {
          const count = typeCounts[type] || 0;
          if (count === 0) return null;

          return (
            <button
              key={type}
              onClick={() => setFilter(type)}
              className={`px-3 py-1 rounded text-xs font-medium transition-colors flex items-center space-x-1 ${
                filter === type
                  ? 'bg-primary-500 text-white'
                  : 'bg-dark-200 text-dark-600 hover:bg-dark-300'
              }`}
            >
              <span>{getMomentIcon(type)}</span>
              <span>
                {type.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')} (
                {count})
              </span>
            </button>
          );
        })}
      </div>

      {/* Timeline */}
      {displayedMoments.length === 0 ? (
        <div className="flex flex-col items-center justify-center bg-dark-50 rounded-lg py-12">
          <div className="text-4xl mb-2">📊</div>
          <p className="text-dark-500">No moments detected yet</p>
          <p className="text-xs text-dark-400 mt-1">Monitoring for anomalies...</p>
        </div>
      ) : (
        <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
          {displayedMoments.map((moment, index) => {
            const colors = getMomentColor(moment.type);
            const severity = getSeverityIndicator(moment.severity);
            const isExpanded = expandedMoment === moment.id;

            return (
              <div
                key={`${moment.id}-${index}`}
                className={`relative border-l-4 ${colors.border} ${colors.bg} rounded-lg p-4 transition-all duration-200 hover:shadow-md cursor-pointer`}
                onClick={() => toggleExpand(moment.id)}
              >
                {/* Timeline connector */}
                {index < displayedMoments.length - 1 && (
                  <div className="absolute left-0 top-full w-0.5 h-3 bg-dark-200" />
                )}

                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    {/* Icon and title */}
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="text-xl">{getMomentIcon(moment.type)}</span>
                      <div className="flex-1">
                        <h4 className="text-sm font-semibold text-dark-800">
                          {moment.description}
                        </h4>
                        <p className="text-xs text-dark-500 mt-0.5">
                          {formatRelativeTime(moment.timestamp)}
                        </p>
                      </div>
                    </div>

                    {/* Severity indicator */}
                    <div className="flex items-center space-x-2 mb-2">
                      <div className={`w-2 h-2 rounded-full ${severity.color}`} />
                      <span className="text-xs font-medium text-dark-600">
                        {severity.label} Severity
                      </span>
                      <span className="text-xs text-dark-400">
                        ({(moment.severity * 100).toFixed(0)}%)
                      </span>
                    </div>

                    {/* Type badge */}
                    <div className="flex items-center space-x-2">
                      <span
                        className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${colors.text} bg-dark-50`}
                      >
                        {moment.type.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                      </span>
                    </div>

                    {/* Expanded details */}
                    {isExpanded && (
                      <div className="mt-3 pt-3 border-t border-dark-200">
                        <div className="space-y-2 text-xs">
                          <div>
                            <span className="text-dark-500">Timestamp:</span>
                            <span className="ml-2 text-dark-700 font-mono">
                              {formatFullTime(moment.timestamp)}
                            </span>
                          </div>
                          <div>
                            <span className="text-dark-500">ID:</span>
                            <span className="ml-2 text-dark-700 font-mono">{moment.id}</span>
                          </div>
                          {moment.metadata && Object.keys(moment.metadata).length > 0 && (
                            <div>
                              <span className="text-dark-500">Metadata:</span>
                              <div className="mt-1 bg-dark-50 rounded p-2 font-mono text-xs">
                                {JSON.stringify(moment.metadata, null, 2)}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Expand indicator */}
                  <button
                    className="text-dark-400 hover:text-dark-600 transition-transform ml-2"
                    style={{
                      transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                    }}
                  >
                    ▼
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Show more indicator */}
      {filteredMoments.length > maxMoments && (
        <div className="mt-4 text-center">
          <p className="text-sm text-dark-500">
            Showing {maxMoments} of {filteredMoments.length} moments
          </p>
        </div>
      )}
    </div>
  );
};
