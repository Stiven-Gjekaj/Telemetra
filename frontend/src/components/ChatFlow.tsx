import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';
import type { ChatRateMetrics } from '../types/metrics';

/**
 * Props for the ChatFlow component
 */
interface ChatFlowProps {
  /** Chat rate metrics to display */
  metrics: ChatRateMetrics | null;
  /** Optional CSS class name */
  className?: string;
  /** Chart height in pixels */
  height?: number;
}

/**
 * Custom tooltip for the chart
 */
interface TooltipProps {
  active?: boolean;
  payload?: Array<{
    value: number;
    payload: { timestamp: number; value: number };
  }>;
  label?: number;
}

const CustomTooltip: React.FC<TooltipProps> = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const date = new Date(data.timestamp);
    const timeString = date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });

    return (
      <div className="bg-dark-50 border border-dark-200 rounded-lg p-3 shadow-lg">
        <p className="text-xs text-dark-500 mb-1">{timeString}</p>
        <p className="text-lg font-bold text-primary-500">
          {data.value.toFixed(1)} <span className="text-sm font-normal">msgs/min</span>
        </p>
      </div>
    );
  }

  return null;
};

/**
 * ChatFlow component displays chat rate over time as a line chart.
 * Shows current rate, average, and peak values with trend visualization.
 *
 * @param props - Component props
 * @returns React component
 */
export const ChatFlow: React.FC<ChatFlowProps> = ({
  metrics,
  className = '',
  height = 300,
}) => {
  const currentRate = metrics?.currentRate ?? 0;
  const averageRate = metrics?.averageRate ?? 0;
  const peakRate = metrics?.peakRate ?? 0;
  const data = metrics?.data ?? [];

  /**
   * Format timestamp for X-axis
   */
  const formatXAxis = (timestamp: number): string => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  /**
   * Format Y-axis values
   */
  const formatYAxis = (value: number): string => {
    if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}k`;
    }
    return value.toString();
  };

  /**
   * Calculate trend direction
   */
  const getTrend = (): { direction: 'up' | 'down' | 'stable'; percentage: number } => {
    if (data.length < 2) {
      return { direction: 'stable', percentage: 0 };
    }

    const recent = data.slice(-5);
    const older = data.slice(-10, -5);

    if (older.length === 0) {
      return { direction: 'stable', percentage: 0 };
    }

    const recentAvg = recent.reduce((sum, pt) => sum + pt.value, 0) / recent.length;
    const olderAvg = older.reduce((sum, pt) => sum + pt.value, 0) / older.length;

    if (olderAvg === 0) {
      return { direction: 'stable', percentage: 0 };
    }

    const percentChange = ((recentAvg - olderAvg) / olderAvg) * 100;

    if (Math.abs(percentChange) < 5) {
      return { direction: 'stable', percentage: 0 };
    }

    return {
      direction: percentChange > 0 ? 'up' : 'down',
      percentage: Math.abs(percentChange),
    };
  };

  const trend = getTrend();

  return (
    <div className={`bg-dark-100 rounded-lg p-6 border border-dark-200 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-dark-800">Chat Activity</h3>
        <div className="flex items-center space-x-2">
          {trend.direction !== 'stable' && (
            <div
              className={`flex items-center space-x-1 text-sm ${
                trend.direction === 'up' ? 'text-green-500' : 'text-red-500'
              }`}
            >
              <span>{trend.direction === 'up' ? '↑' : '↓'}</span>
              <span>{trend.percentage.toFixed(1)}%</span>
            </div>
          )}
        </div>
      </div>

      {/* Current rate display */}
      <div className="mb-4">
        <div className="flex items-baseline space-x-2">
          <span className="text-4xl font-bold text-primary-500">
            {currentRate.toFixed(1)}
          </span>
          <span className="text-sm text-dark-500">messages per minute</span>
        </div>
      </div>

      {/* Chart */}
      {data.length > 0 ? (
        <div className="mb-4">
          <ResponsiveContainer width="100%" height={height}>
            <AreaChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
              <defs>
                <linearGradient id="chatRateGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#3f3f46" opacity={0.3} />
              <XAxis
                dataKey="timestamp"
                tickFormatter={formatXAxis}
                stroke="#71717a"
                style={{ fontSize: '12px' }}
                tickCount={5}
              />
              <YAxis
                tickFormatter={formatYAxis}
                stroke="#71717a"
                style={{ fontSize: '12px' }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#0ea5e9"
                strokeWidth={2}
                fill="url(#chatRateGradient)"
                animationDuration={300}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div
          className="flex items-center justify-center bg-dark-50 rounded-lg mb-4"
          style={{ height: `${height}px` }}
        >
          <p className="text-dark-500">Waiting for chat data...</p>
        </div>
      )}

      {/* Stats grid */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-dark-50 rounded-lg p-3">
          <p className="text-xs text-dark-500 mb-1">Average Rate</p>
          <p className="text-xl font-bold text-dark-800">
            {averageRate.toFixed(1)}
            <span className="text-sm font-normal text-dark-500 ml-1">msg/min</span>
          </p>
        </div>
        <div className="bg-dark-50 rounded-lg p-3">
          <p className="text-xs text-dark-500 mb-1">Peak Rate</p>
          <p className="text-xl font-bold text-dark-800">
            {peakRate.toFixed(1)}
            <span className="text-sm font-normal text-dark-500 ml-1">msg/min</span>
          </p>
        </div>
      </div>

      {/* Activity indicator */}
      <div className="mt-4 pt-4 border-t border-dark-200">
        <div className="flex items-center justify-between">
          <span className="text-xs text-dark-500">Activity Level</span>
          <div className="flex items-center space-x-2">
            {(() => {
              const activityLevel =
                peakRate > 0 ? (currentRate / peakRate) * 100 : 0;

              let label = 'Low';
              let color = 'bg-dark-500';

              if (activityLevel > 70) {
                label = 'Very High';
                color = 'bg-red-500';
              } else if (activityLevel > 50) {
                label = 'High';
                color = 'bg-orange-500';
              } else if (activityLevel > 30) {
                label = 'Medium';
                color = 'bg-yellow-500';
              } else if (activityLevel > 10) {
                label = 'Low';
                color = 'bg-green-500';
              }

              return (
                <>
                  <div className={`w-2 h-2 rounded-full ${color}`} />
                  <span className="text-xs font-medium text-dark-700">{label}</span>
                </>
              );
            })()}
          </div>
        </div>
      </div>
    </div>
  );
};
