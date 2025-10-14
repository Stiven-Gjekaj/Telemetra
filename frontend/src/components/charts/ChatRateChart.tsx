import { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { ChatMetrics, Moment } from '../../types';
import './Chart.css';

interface ChatRateChartProps {
  data: ChatMetrics[];
  moments: Moment[];
}

function ChatRateChart({ data, moments }: ChatRateChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!svgRef.current || !containerRef.current || data.length === 0) return;

    // Clear previous chart
    d3.select(svgRef.current).selectAll('*').remove();

    const container = containerRef.current;
    const margin = { top: 20, right: 30, bottom: 40, left: 60 };
    const width = container.clientWidth - margin.left - margin.right;
    const height = 300 - margin.top - margin.bottom;

    const svg = d3.select(svgRef.current)
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom)
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Parse timestamps
    const parseTime = d3.timeParse('%Y-%m-%dT%H:%M:%S');
    const dataPoints = data.map(d => ({
      timestamp: parseTime(d.window_start.split('.')[0]) || new Date(),
      messageCount: d.message_count,
      uniqueChatters: d.unique_chatters
    }));

    // X scale
    const x = d3.scaleTime()
      .domain(d3.extent(dataPoints, d => d.timestamp) as [Date, Date])
      .range([0, width]);

    // Y scale
    const maxMessages = d3.max(dataPoints, d => d.messageCount) || 0;
    const y = d3.scaleLinear()
      .domain([0, maxMessages * 1.1])
      .range([height, 0]);

    // Line generator for messages
    const messageLine = d3.line<{ timestamp: Date; messageCount: number }>()
      .x(d => x(d.timestamp))
      .y(d => y(d.messageCount))
      .curve(d3.curveMonotoneX);

    // Add gradient
    const gradient = svg.append('defs')
      .append('linearGradient')
      .attr('id', 'chat-gradient')
      .attr('x1', '0%')
      .attr('y1', '0%')
      .attr('x2', '0%')
      .attr('y2', '100%');

    gradient.append('stop')
      .attr('offset', '0%')
      .attr('style', 'stop-color:#00f593;stop-opacity:0.6');

    gradient.append('stop')
      .attr('offset', '100%')
      .attr('style', 'stop-color:#00f593;stop-opacity:0');

    // Add area for messages
    const area = d3.area<{ timestamp: Date; messageCount: number }>()
      .x(d => x(d.timestamp))
      .y0(height)
      .y1(d => y(d.messageCount))
      .curve(d3.curveMonotoneX);

    svg.append('path')
      .datum(dataPoints)
      .attr('fill', 'url(#chat-gradient)')
      .attr('d', area);

    // Add line for messages
    svg.append('path')
      .datum(dataPoints)
      .attr('fill', 'none')
      .attr('stroke', '#00f593')
      .attr('stroke-width', 2)
      .attr('d', messageLine);

    // Add moment markers (anomalies)
    const momentMarkers = moments
      .filter(m => m.moment_type === 'anomaly')
      .map(m => ({
        timestamp: parseTime(m.timestamp.split('.')[0]) || new Date(),
        severity: m.severity,
        description: m.description
      }))
      .filter(m => x(m.timestamp) >= 0 && x(m.timestamp) <= width);

    svg.selectAll('.moment-marker')
      .data(momentMarkers)
      .enter()
      .append('line')
      .attr('class', 'moment-marker')
      .attr('x1', d => x(d.timestamp))
      .attr('x2', d => x(d.timestamp))
      .attr('y1', 0)
      .attr('y2', height)
      .attr('stroke', '#eb0400')
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', '4')
      .attr('opacity', 0.8);

    // X axis
    svg.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(x).ticks(6))
      .attr('color', '#adadb8')
      .selectAll('text')
      .style('font-size', '12px');

    // Y axis
    svg.append('g')
      .call(d3.axisLeft(y).ticks(5))
      .attr('color', '#adadb8')
      .selectAll('text')
      .style('font-size', '12px');

    // Y axis label
    svg.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', 0 - margin.left)
      .attr('x', 0 - (height / 2))
      .attr('dy', '1em')
      .style('text-anchor', 'middle')
      .style('fill', '#adadb8')
      .style('font-size', '12px')
      .text('Messages per Minute');

  }, [data, moments]);

  return (
    <div ref={containerRef} className="chart-wrapper">
      <svg ref={svgRef}></svg>
    </div>
  );
}

export default ChatRateChart;
