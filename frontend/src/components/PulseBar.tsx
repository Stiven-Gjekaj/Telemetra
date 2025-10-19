import React, { useEffect, useState } from 'react';
import type { ViewerMetrics } from '../types/metrics';

/**
 * Props for the PulseBar component
 */
interface PulseBarProps {
  /** Viewer metrics to display */
  metrics: ViewerMetrics | null;
  /** Optional CSS class name */
  className?: string;
}

/**
 * PulseBar component displays current viewer count with an animated pulse effect.
 * The pulse intensity increases when viewer count changes significantly.
 *
 * @param props - Component props
 * @returns React component
 */
export const PulseBar: React.FC<PulseBarProps> = ({ metrics, className = '' }) => {
  const [previousCount, setPreviousCount] = useState<number>(0);
  const [isIncreasing, setIsIncreasing] = useState<boolean>(false);
  const [pulseIntensity, setPulseIntensity] = useState<number>(0);

  const currentCount = metrics?.current ?? 0;
  const peakCount = metrics?.peak ?? 0;
  const averageCount = metrics?.average ?? 0;

  /**
   * Calculate percentage change for pulse intensity
   */
  useEffect(() => {
    if (previousCount > 0 && currentCount !== previousCount) {
      const percentChange = Math.abs((currentCount - previousCount) / previousCount);
      setIsIncreasing(currentCount > previousCount);
      setPulseIntensity(Math.min(percentChange * 100, 100));

      // Reset pulse intensity after animation
      const timer = setTimeout(() => setPulseIntensity(0), 1000);
      return () => clearTimeout(timer);
    }
    setPreviousCount(currentCount);
  }, [currentCount, previousCount]);

  /**
   * Format large numbers with K/M suffix
   */
  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`;
    }
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`;
    }
    return num.toString();
  };

  /**
   * Calculate fill percentage for visual bar
   */
  const fillPercentage = peakCount > 0 ? (currentCount / peakCount) * 100 : 0;

  return (
    <div className={`bg-dark-100 rounded-lg p-6 border border-dark-200 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-dark-800">Live Viewers</h3>
        <div className="flex items-center space-x-2">
          <div
            className={`w-3 h-3 rounded-full ${
              pulseIntensity > 0 ? 'animate-pulse' : ''
            } ${isIncreasing ? 'bg-green-500' : 'bg-primary-500'}`}
            style={{
              boxShadow: pulseIntensity > 0
                ? `0 0 ${pulseIntensity / 5}px ${
                    isIncreasing ? 'rgb(34 197 94)' : 'rgb(14 165 233)'
                  }`
                : 'none',
            }}
          />
          <span className="text-sm text-dark-500">Live</span>
        </div>
      </div>

      {/* Main viewer count display */}
      <div className="mb-6">
        <div className="flex items-baseline space-x-2">
          <span
            className={`text-5xl font-bold transition-colors duration-300 ${
              pulseIntensity > 0 && isIncreasing
                ? 'text-green-500'
                : pulseIntensity > 0
                ? 'text-red-500'
                : 'text-primary-500'
            }`}
          >
            {formatNumber(currentCount)}
          </span>
          {previousCount > 0 && currentCount !== previousCount && (
            <span
              className={`text-lg font-medium ${
                isIncreasing ? 'text-green-500' : 'text-red-500'
              }`}
            >
              {isIncreasing ? '↑' : '↓'}{' '}
              {formatNumber(Math.abs(currentCount - previousCount))}
            </span>
          )}
        </div>
        <p className="text-sm text-dark-500 mt-1">viewers watching now</p>
      </div>

      {/* Visual progress bar */}
      <div className="relative w-full h-3 bg-dark-200 rounded-full overflow-hidden mb-4">
        <div
          className={`absolute top-0 left-0 h-full rounded-full transition-all duration-500 ease-out ${
            pulseIntensity > 0 && isIncreasing
              ? 'bg-gradient-to-r from-green-500 to-green-400'
              : 'bg-gradient-to-r from-primary-600 to-primary-400'
          }`}
          style={{
            width: `${Math.min(fillPercentage, 100)}%`,
          }}
        >
          {pulseIntensity > 0 && (
            <div
              className="absolute inset-0 bg-white opacity-30 animate-pulse"
              style={{
                animationDuration: '0.5s',
              }}
            />
          )}
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-dark-50 rounded-lg p-3">
          <p className="text-xs text-dark-500 mb-1">Peak</p>
          <p className="text-xl font-bold text-dark-800">
            {formatNumber(peakCount)}
          </p>
        </div>
        <div className="bg-dark-50 rounded-lg p-3">
          <p className="text-xs text-dark-500 mb-1">Average</p>
          <p className="text-xl font-bold text-dark-800">
            {formatNumber(averageCount)}
          </p>
        </div>
      </div>

      {/* Historical trend indicator */}
      {metrics?.history && metrics.history.length > 1 && (
        <div className="mt-4 pt-4 border-t border-dark-200">
          <div className="flex items-center justify-between text-xs text-dark-500">
            <span>Trend</span>
            <span className="flex items-center space-x-1">
              {(() => {
                const history = metrics.history;
                const recentAvg =
                  history
                    .slice(-5)
                    .reduce((sum, pt) => sum + pt.value, 0) / Math.min(5, history.length);
                const olderAvg =
                  history
                    .slice(-10, -5)
                    .reduce((sum, pt) => sum + pt.value, 0) /
                  Math.min(5, history.length - 5);

                if (olderAvg === 0) return <span>Stable</span>;

                const trendChange = ((recentAvg - olderAvg) / olderAvg) * 100;

                if (Math.abs(trendChange) < 5) {
                  return <span className="text-dark-600">Stable</span>;
                } else if (trendChange > 0) {
                  return (
                    <span className="text-green-500">
                      Growing +{trendChange.toFixed(1)}%
                    </span>
                  );
                } else {
                  return (
                    <span className="text-red-500">
                      Declining {trendChange.toFixed(1)}%
                    </span>
                  );
                }
              })()}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
