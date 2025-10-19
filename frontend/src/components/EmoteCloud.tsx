import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import cloud from 'd3-cloud';
import type { Emote } from '../types/metrics';

/**
 * Props for the EmoteCloud component
 */
interface EmoteCloudProps {
  /** Array of emotes with frequency counts */
  emotes: Emote[];
  /** Optional CSS class name */
  className?: string;
  /** Width of the cloud container */
  width?: number;
  /** Height of the cloud container */
  height?: number;
  /** Maximum number of emotes to display */
  maxEmotes?: number;
}

/**
 * Internal word cloud data structure
 */
interface CloudWord {
  text: string;
  size: number;
  count: number;
  x?: number;
  y?: number;
  rotate?: number;
}

/**
 * EmoteCloud component displays top emotes as a bubble chart using D3.
 * Bubble size is proportional to emote frequency.
 *
 * @param props - Component props
 * @returns React component
 */
export const EmoteCloud: React.FC<EmoteCloudProps> = ({
  emotes,
  className = '',
  width = 600,
  height = 400,
  maxEmotes = 30,
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [hoveredEmote, setHoveredEmote] = useState<string | null>(null);
  const [selectedView, setSelectedView] = useState<'cloud' | 'list'>('cloud');

  /**
   * Generate and render the word cloud
   */
  useEffect(() => {
    if (!svgRef.current || emotes.length === 0 || selectedView === 'list') {
      return;
    }

    // Clear previous content
    d3.select(svgRef.current).selectAll('*').remove();

    // Sort and limit emotes
    const topEmotes = [...emotes]
      .sort((a, b) => b.count - a.count)
      .slice(0, maxEmotes);

    // Calculate size scale
    const maxCount = Math.max(...topEmotes.map(e => e.count), 1);
    const minCount = Math.min(...topEmotes.map(e => e.count), 1);

    const sizeScale = d3
      .scaleLinear()
      .domain([minCount, maxCount])
      .range([16, 72]);

    // Prepare word cloud data
    const words: CloudWord[] = topEmotes.map(emote => ({
      text: emote.name,
      size: sizeScale(emote.count),
      count: emote.count,
    }));

    // Create word cloud layout
    const layout = cloud<CloudWord>()
      .size([width, height])
      .words(words)
      .padding(5)
      .rotate(() => 0)
      .fontSize(d => d.size)
      .on('end', draw);

    layout.start();

    /**
     * Draw the word cloud
     */
    function draw(computedWords: CloudWord[]) {
      const svg = d3
        .select(svgRef.current)
        .attr('width', width)
        .attr('height', height)
        .attr('viewBox', `0 0 ${width} ${height}`);

      const g = svg
        .append('g')
        .attr('transform', `translate(${width / 2},${height / 2})`);

      // Color scale
      const colorScale = d3
        .scaleSequential(d3.interpolateBlues)
        .domain([minCount, maxCount]);

      // Create text elements
      const text = g
        .selectAll<SVGTextElement, CloudWord>('text')
        .data(computedWords)
        .enter()
        .append('text')
        .style('font-size', d => `${d.size}px`)
        .style('font-family', 'Arial, sans-serif')
        .style('font-weight', 'bold')
        .style('fill', d => colorScale(d.count))
        .style('cursor', 'pointer')
        .style('transition', 'all 0.2s')
        .attr('text-anchor', 'middle')
        .attr('transform', d => `translate(${d.x},${d.y})rotate(${d.rotate})`)
        .text(d => d.text)
        .on('mouseenter', function (event, d) {
          setHoveredEmote(`${d.text}: ${d.count}`);
          d3.select(this)
            .transition()
            .duration(200)
            .style('fill', '#0ea5e9')
            .attr('transform', function () {
              const currentTransform = d3.select(this).attr('transform');
              const scale = 1.2;
              return `${currentTransform} scale(${scale})`;
            });
        })
        .on('mouseleave', function (event, d) {
          setHoveredEmote(null);
          d3.select(this)
            .transition()
            .duration(200)
            .style('fill', colorScale(d.count))
            .attr('transform', `translate(${d.x},${d.y})rotate(${d.rotate})`);
        });

      // Animate entrance
      text
        .style('opacity', 0)
        .transition()
        .duration(500)
        .style('opacity', 1);
    }
  }, [emotes, width, height, maxEmotes, selectedView]);

  /**
   * Sort emotes for list view
   */
  const sortedEmotes = [...emotes].sort((a, b) => b.count - a.count).slice(0, maxEmotes);

  /**
   * Calculate bar width percentage
   */
  const getBarWidth = (count: number): number => {
    const maxCount = Math.max(...emotes.map(e => e.count), 1);
    return (count / maxCount) * 100;
  };

  return (
    <div className={`bg-dark-100 rounded-lg p-6 border border-dark-200 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-dark-800">Top Emotes</h3>
        <div className="flex space-x-2">
          <button
            onClick={() => setSelectedView('cloud')}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              selectedView === 'cloud'
                ? 'bg-primary-500 text-white'
                : 'bg-dark-200 text-dark-600 hover:bg-dark-300'
            }`}
          >
            Cloud
          </button>
          <button
            onClick={() => setSelectedView('list')}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              selectedView === 'list'
                ? 'bg-primary-500 text-white'
                : 'bg-dark-200 text-dark-600 hover:bg-dark-300'
            }`}
          >
            List
          </button>
        </div>
      </div>

      {/* Content */}
      {emotes.length === 0 ? (
        <div
          className="flex items-center justify-center bg-dark-50 rounded-lg"
          style={{ height: `${height}px` }}
        >
          <p className="text-dark-500">No emote data available</p>
        </div>
      ) : selectedView === 'cloud' ? (
        <>
          {/* Word Cloud */}
          <div className="relative bg-dark-50 rounded-lg overflow-hidden">
            <svg ref={svgRef} className="w-full" style={{ minHeight: `${height}px` }} />
            {hoveredEmote && (
              <div className="absolute top-4 right-4 bg-dark-100 border border-dark-200 rounded-lg px-3 py-2 shadow-lg">
                <p className="text-sm font-medium text-dark-800">{hoveredEmote}</p>
              </div>
            )}
          </div>

          {/* Legend */}
          <div className="mt-4 flex items-center justify-center space-x-4 text-xs text-dark-500">
            <span>Less frequent</span>
            <div className="flex space-x-1">
              {[1, 2, 3, 4, 5].map(i => (
                <div
                  key={i}
                  className="w-6 h-3 rounded"
                  style={{
                    backgroundColor: d3.interpolateBlues(i * 0.2),
                  }}
                />
              ))}
            </div>
            <span>More frequent</span>
          </div>
        </>
      ) : (
        /* List View */
        <div
          className="space-y-2 overflow-y-auto pr-2"
          style={{ maxHeight: `${height}px` }}
        >
          {sortedEmotes.map((emote, index) => (
            <div
              key={`${emote.name}-${index}`}
              className="bg-dark-50 rounded-lg p-3 hover:bg-dark-200 transition-colors"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-dark-800 text-sm">{emote.name}</span>
                <span className="text-primary-500 font-bold">{emote.count}</span>
              </div>
              <div className="relative w-full h-2 bg-dark-100 rounded-full overflow-hidden">
                <div
                  className="absolute top-0 left-0 h-full bg-gradient-to-r from-primary-600 to-primary-400 transition-all duration-500"
                  style={{ width: `${getBarWidth(emote.count)}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Stats */}
      <div className="mt-4 pt-4 border-t border-dark-200">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-dark-500 mb-1">Unique Emotes</p>
            <p className="text-xl font-bold text-dark-800">{emotes.length}</p>
          </div>
          <div>
            <p className="text-xs text-dark-500 mb-1">Total Usage</p>
            <p className="text-xl font-bold text-dark-800">
              {emotes.reduce((sum, e) => sum + e.count, 0).toLocaleString()}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
