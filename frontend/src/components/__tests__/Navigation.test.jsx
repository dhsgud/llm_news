import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import Navigation from '../Navigation';

describe('Navigation Component', () => {
  it('renders the application title', () => {
    render(
      <BrowserRouter>
        <Navigation />
      </BrowserRouter>
    );
    
    expect(screen.getByText('Market Sentiment Analyzer')).toBeInTheDocument();
  });

  it('renders all navigation items', () => {
    render(
      <BrowserRouter>
        <Navigation />
      </BrowserRouter>
    );
    
    expect(screen.getByText('Market Analysis')).toBeInTheDocument();
    expect(screen.getByText('Stocks')).toBeInTheDocument();
    expect(screen.getByText('Auto Trading')).toBeInTheDocument();
  });

  it('highlights the active route', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Navigation />
      </MemoryRouter>
    );
    
    const marketAnalysisLink = screen.getByText('Market Analysis');
    expect(marketAnalysisLink).toHaveClass('bg-blue-500', 'text-white');
  });

  it('does not highlight inactive routes', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Navigation />
      </MemoryRouter>
    );
    
    const stocksLink = screen.getByText('Stocks');
    expect(stocksLink).not.toHaveClass('bg-blue-500');
    expect(stocksLink).toHaveClass('text-gray-700');
  });
});
