import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

interface PulseBarProps {
  value: number;
  max: number;
  label: string;
  color?: string;
}

const PulseBar: React.FC<PulseBarProps> = ({ value, max, label, color = '#9146FF' }) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current);
    const width = svgRef.current.clientWidth;
    const height = 80;
    const margin = { top: 10, right: 20, bottom: 30, left: 20 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    svg.selectAll('*').remove();

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Background bar
    g.append('rect')
      .attr('x', 0)
      .attr('y', 0)
      .attr('width', innerWidth)
      .attr('height', innerHeight)
      .attr('fill', '#0e0e10')
      .attr('rx', 4);

    // Value bar with animation
    const percentage = Math.min((value / max) * 100, 100);
    const barWidth = (percentage / 100) * innerWidth;

    g.append('rect')
      .attr('x', 0)
      .attr('y', 0)
      .attr('width', 0)
      .attr('height', innerHeight)
      .attr('fill', color)
      .attr('rx', 4)
      .transition()
      .duration(800)
      .ease(d3.easeElasticOut)
      .attr('width', barWidth);

    // Pulse effect
    const pulse = g.append('rect')
      .attr('x', 0)
      .attr('y', 0)
      .attr('width', barWidth)
      .attr('height', innerHeight)
      .attr('fill', color)
      .attr('opacity', 0.3)
      .attr('rx', 4);

    pulse.transition()
      .duration(1500)
      .ease(d3.easeSinInOut)
      .attr('opacity', 0)
      .attr('width', barWidth + 10)
      .on('end', function repeat() {
        d3.select(this)
          .attr('opacity', 0.3)
          .attr('width', barWidth)
          .transition()
          .duration(1500)
          .ease(d3.easeSinInOut)
          .attr('opacity', 0)
          .attr('width', barWidth + 10)
          .on('end', repeat);
      });

    // Value text
    g.append('text')
      .attr('x', innerWidth / 2)
      .attr('y', innerHeight / 2)
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .attr('fill', '#efeff1')
      .attr('font-weight', 'bold')
      .attr('font-size', '20px')
      .style('text-shadow', '0 0 4px rgba(0,0,0,0.8)')
      .text(`${value.toLocaleString()} ${label}`);

    // Percentage text
    g.append('text')
      .attr('x', innerWidth - 5)
      .attr('y', innerHeight + 20)
      .attr('text-anchor', 'end')
      .attr('fill', '#adadb8')
      .attr('font-size', '12px')
      .text(`${percentage.toFixed(1)}% of max`);

  }, [value, max, label, color]);

  return (
    <div style={{ width: '100%' }}>
      <svg ref={svgRef} style={{ width: '100%', height: '110px' }}></svg>
    </div>
  );
};

export default PulseBar;
