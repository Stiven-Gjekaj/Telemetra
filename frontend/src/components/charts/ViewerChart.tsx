import { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { ViewerMetrics, Moment } from '../../types';
import './Chart.css';

interface ViewerChartProps {
  data: ViewerMetrics[];
  moments: Moment[];
}

function ViewerChart({ data, moments }: ViewerChartProps) {
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
      timestamp: parseTime(d.timestamp.split('.')[0]) || new Date(),
      viewerCount: d.viewer_count
    }));

    // X scale
    const x = d3.scaleTime()
      .domain(d3.extent(dataPoints, d => d.timestamp) as [Date, Date])
      .range([0, width]);

    // Y scale
    const maxViewers = d3.max(dataPoints, d => d.viewerCount) || 0;
    const y = d3.scaleLinear()
      .domain([0, maxViewers * 1.1])
      .range([height, 0]);

    // Line generator
    const line = d3.line<{ timestamp: Date; viewerCount: number }>()
      .x(d => x(d.timestamp))
      .y(d => y(d.viewerCount))
      .curve(d3.curveMonotoneX);

    // Add gradient
    const gradient = svg.append('defs')
      .append('linearGradient')
      .attr('id', 'viewer-gradient')
      .attr('x1', '0%')
      .attr('y1', '0%')
      .attr('x2', '0%')
      .attr('y2', '100%');

    gradient.append('stop')
      .attr('offset', '0%')
      .attr('style', 'stop-color:#9147ff;stop-opacity:0.6');

    gradient.append('stop')
      .attr('offset', '100%')
      .attr('style', 'stop-color:#9147ff;stop-opacity:0');

    // Add area
    const area = d3.area<{ timestamp: Date; viewerCount: number }>()
      .x(d => x(d.timestamp))
      .y0(height)
      .y1(d => y(d.viewerCount))
      .curve(d3.curveMonotoneX);

    svg.append('path')
      .datum(dataPoints)
      .attr('fill', 'url(#viewer-gradient)')
      .attr('d', area);

    // Add line
    svg.append('path')
      .datum(dataPoints)
      .attr('fill', 'none')
      .attr('stroke', '#9147ff')
      .attr('stroke-width', 2)
      .attr('d', line);

    // Add moment markers
    const momentMarkers = moments
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
      .attr('stroke', d => d.severity >= 0.8 ? '#eb0400' : '#ff9500')
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', '4')
      .attr('opacity', 0.6);

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
      .text('Viewer Count');

  }, [data, moments]);

  return (
    <div ref={containerRef} className="chart-wrapper">
      <svg ref={svgRef}></svg>
    </div>
  );
}

export default ViewerChart;
