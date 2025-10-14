import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

interface ChatData {
  window_start: string;
  message_count: number;
  unique_chatters: number;
}

interface ChatRateChartProps {
  data: ChatData[];
}

const ChatRateChart: React.FC<ChatRateChartProps> = ({ data }) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || data.length === 0) return;

    const svg = d3.select(svgRef.current);
    const width = svgRef.current.clientWidth;
    const height = 300;
    const margin = { top: 20, right: 80, bottom: 40, left: 60 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    svg.selectAll('*').remove();

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Parse data
    const parsedData = [...data]
      .reverse()
      .map(d => ({
        time: new Date(d.window_start),
        messageCount: d.message_count,
        uniqueChatters: d.unique_chatters
      }));

    // Create scales
    const xScale = d3.scaleTime()
      .domain(d3.extent(parsedData, d => d.time) as [Date, Date])
      .range([0, innerWidth]);

    const yScale = d3.scaleLinear()
      .domain([0, d3.max(parsedData, d => d.messageCount) || 100])
      .range([innerHeight, 0]);

    // Create axes
    const xAxis = d3.axisBottom(xScale)
      .ticks(6)
      .tickFormat(d3.timeFormat('%H:%M') as any);

    const yAxis = d3.axisLeft(yScale)
      .ticks(5);

    // Append x-axis
    g.append('g')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(xAxis)
      .attr('color', '#adadb8');

    // Append y-axis
    g.append('g')
      .call(yAxis)
      .attr('color', '#adadb8');

    // Create line generator
    const line = d3.line<any>()
      .x(d => xScale(d.time))
      .y(d => yScale(d.messageCount))
      .curve(d3.curveMonotoneX);

    // Create area generator for fill
    const area = d3.area<any>()
      .x(d => xScale(d.time))
      .y0(innerHeight)
      .y1(d => yScale(d.messageCount))
      .curve(d3.curveMonotoneX);

    // Append area with gradient
    g.append('path')
      .datum(parsedData)
      .attr('fill', '#9146FF')
      .attr('fill-opacity', 0.2)
      .attr('d', area);

    // Append line path
    g.append('path')
      .datum(parsedData)
      .attr('fill', 'none')
      .attr('stroke', '#9146FF')
      .attr('stroke-width', 2.5)
      .attr('d', line);

    // Add data points
    g.selectAll('circle')
      .data(parsedData)
      .enter()
      .append('circle')
      .attr('cx', d => xScale(d.time))
      .attr('cy', d => yScale(d.messageCount))
      .attr('r', 3)
      .attr('fill', '#00F2EA')
      .attr('stroke', '#0e0e10')
      .attr('stroke-width', 1.5);

    // Y-axis label
    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -innerHeight / 2)
      .attr('y', -45)
      .attr('text-anchor', 'middle')
      .attr('fill', '#adadb8')
      .attr('font-size', '12px')
      .text('Messages per Minute');

  }, [data]);

  return (
    <div style={{ width: '100%' }}>
      <svg ref={svgRef} style={{ width: '100%', height: '330px' }}></svg>
    </div>
  );
};

export default ChatRateChart;