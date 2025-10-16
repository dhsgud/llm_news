import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import DailySentimentChart from '../DailySentimentChart';

describe('DailySentimentChart Component', () => {
  const mockDailyData = [
    { date: '2025-10-01', score: 0.5 },
    { date: '2025-10-02', score: -1.5 },
    { date: '2025-10-03', score: 0.0 },
    { date: '2025-10-04', score: 1.0 },
    { date: '2025-10-05', score: -0.8 },
    { date: '2025-10-06', score: 0.3 },
    { date: '2025-10-07', score: 0.7 },
  ];

  it('renders the chart with title', () => {
    render(<DailySentimentChart dailyData={mockDailyData} />);
    
    // Chart.js renders canvas element
    const canvas = document.querySelector('canvas');
    expect(canvas).toBeInTheDocument();
  });

  it('handles empty data array', () => {
    render(<DailySentimentChart dailyData={[]} />);
    
    const canvas = document.querySelector('canvas');
    expect(canvas).toBeInTheDocument();
  });

  it('handles single data point', () => {
    const singleData = [{ date: '2025-10-01', score: 0.5 }];
    render(<DailySentimentChart dailyData={singleData} />);
    
    const canvas = document.querySelector('canvas');
    expect(canvas).toBeInTheDocument();
  });

  it('renders with positive scores', () => {
    const positiveData = [
      { date: '2025-10-01', score: 0.5 },
      { date: '2025-10-02', score: 1.0 },
    ];
    render(<DailySentimentChart dailyData={positiveData} />);
    
    const canvas = document.querySelector('canvas');
    expect(canvas).toBeInTheDocument();
  });

  it('renders with negative scores', () => {
    const negativeData = [
      { date: '2025-10-01', score: -0.5 },
      { date: '2025-10-02', score: -1.5 },
    ];
    render(<DailySentimentChart dailyData={negativeData} />);
    
    const canvas = document.querySelector('canvas');
    expect(canvas).toBeInTheDocument();
  });

  it('renders with mixed scores', () => {
    render(<DailySentimentChart dailyData={mockDailyData} />);
    
    const canvas = document.querySelector('canvas');
    expect(canvas).toBeInTheDocument();
  });
});
