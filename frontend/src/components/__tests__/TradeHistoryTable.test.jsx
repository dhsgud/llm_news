import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import TradeHistoryTable from '../TradeHistoryTable';

describe('TradeHistoryTable', () => {
  const mockTrades = [
    {
      id: 1,
      symbol: 'AAPL',
      action: 'buy',
      quantity: 10,
      price: 150000,
      timestamp: '2025-10-11T10:00:00',
      status: '완료'
    },
    {
      id: 2,
      symbol: 'GOOGL',
      action: 'sell',
      quantity: 5,
      price: 200000,
      timestamp: '2025-10-11T11:00:00',
      status: '완료'
    }
  ];

  it('renders trade history table', () => {
    render(<TradeHistoryTable trades={mockTrades} isLoading={false} />);
    
    expect(screen.getByText('거래 내역')).toBeInTheDocument();
    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('GOOGL')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(<TradeHistoryTable trades={[]} isLoading={true} />);
    
    expect(screen.getByText('거래 내역')).toBeInTheDocument();
    // Loading spinner should be present
    const spinner = document.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('shows empty state when no trades', () => {
    render(<TradeHistoryTable trades={[]} isLoading={false} />);
    
    expect(screen.getByText('거래 내역이 없습니다')).toBeInTheDocument();
  });

  it('displays buy and sell actions correctly', () => {
    render(<TradeHistoryTable trades={mockTrades} isLoading={false} />);
    
    expect(screen.getByText('매수')).toBeInTheDocument();
    expect(screen.getByText('매도')).toBeInTheDocument();
  });
});
