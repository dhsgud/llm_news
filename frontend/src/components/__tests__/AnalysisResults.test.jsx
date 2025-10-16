import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import AnalysisResults from '../AnalysisResults';

describe('AnalysisResults Component', () => {
  const mockResultStrongBuy = {
    buy_sell_ratio: 85,
    trend_summary: 'Market shows strong positive sentiment with bullish indicators.',
    vix: 15.5,
  };

  const mockResultStrongSell = {
    buy_sell_ratio: 20,
    trend_summary: 'Market shows negative sentiment with bearish indicators.',
    vix: 28.3,
  };

  const mockResultNeutral = {
    buy_sell_ratio: 50,
    trend_summary: 'Market shows mixed signals with no clear direction.',
    vix: 18.0,
  };

  it('renders strong buy recommendation for high ratio', () => {
    render(<AnalysisResults result={mockResultStrongBuy} />);
    
    expect(screen.getByText('강력 매수')).toBeInTheDocument();
    expect(screen.getByText('85')).toBeInTheDocument();
  });

  it('renders strong sell recommendation for low ratio', () => {
    render(<AnalysisResults result={mockResultStrongSell} />);
    
    expect(screen.getByText('강력 매도')).toBeInTheDocument();
    expect(screen.getByText('20')).toBeInTheDocument();
  });

  it('renders neutral recommendation for medium ratio', () => {
    render(<AnalysisResults result={mockResultNeutral} />);
    
    expect(screen.getByText('중립')).toBeInTheDocument();
    expect(screen.getByText('50')).toBeInTheDocument();
  });

  it('displays the trend summary', () => {
    render(<AnalysisResults result={mockResultStrongBuy} />);
    
    expect(screen.getByText('Market Trend Summary')).toBeInTheDocument();
    expect(screen.getByText('Market shows strong positive sentiment with bullish indicators.')).toBeInTheDocument();
  });

  it('displays VIX information when provided', () => {
    render(<AnalysisResults result={mockResultStrongBuy} />);
    
    expect(screen.getByText('VIX Index:')).toBeInTheDocument();
    expect(screen.getByText('15.50')).toBeInTheDocument();
    expect(screen.getByText('Market volatility indicator')).toBeInTheDocument();
  });

  it('does not display VIX when not provided', () => {
    const resultWithoutVix = {
      buy_sell_ratio: 75,
      trend_summary: 'Test summary',
    };
    
    render(<AnalysisResults result={resultWithoutVix} />);
    
    expect(screen.queryByText('VIX Index:')).not.toBeInTheDocument();
  });

  it('applies correct color classes for strong buy', () => {
    render(<AnalysisResults result={mockResultStrongBuy} />);
    
    const badge = screen.getByText('강력 매수');
    expect(badge).toHaveClass('text-green-600');
    expect(badge).toHaveClass('bg-green-50');
  });

  it('applies correct color classes for strong sell', () => {
    render(<AnalysisResults result={mockResultStrongSell} />);
    
    const badge = screen.getByText('강력 매도');
    expect(badge).toHaveClass('text-red-600');
    expect(badge).toHaveClass('bg-red-50');
  });

  it('applies correct color classes for neutral', () => {
    render(<AnalysisResults result={mockResultNeutral} />);
    
    const badge = screen.getByText('중립');
    expect(badge).toHaveClass('text-yellow-600');
    expect(badge).toHaveClass('bg-yellow-50');
  });
});
