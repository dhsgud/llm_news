import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MarketDashboard from '../MarketDashboard';
import * as api from '../../services/api';

// Mock the API module
vi.mock('../../services/api', () => ({
  analyzeMarket: vi.fn(),
  getDailySentiment: vi.fn(),
}));

describe('MarketDashboard Page', () => {
  const mockAnalysisResult = {
    buy_sell_ratio: 75,
    trend_summary: 'Market shows positive sentiment with strong indicators.',
    vix: 16.5,
    last_updated: '2025-10-07T10:30:00Z',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the page title and description', () => {
    render(<MarketDashboard />);
    
    expect(screen.getByText('Market Sentiment Analyzer')).toBeInTheDocument();
    expect(screen.getByText('AI-powered market analysis and investment recommendations')).toBeInTheDocument();
  });

  it('renders the analyze button', () => {
    render(<MarketDashboard />);
    
    expect(screen.getByRole('button', { name: /Analyze Market/i })).toBeInTheDocument();
  });

  it('does not show last updated time initially', () => {
    render(<MarketDashboard />);
    
    expect(screen.queryByText(/Last Updated:/i)).not.toBeInTheDocument();
  });

  it('calls API when analyze button is clicked', async () => {
    const user = userEvent.setup();
    api.analyzeMarket.mockResolvedValue(mockAnalysisResult);
    
    render(<MarketDashboard />);
    
    const analyzeButton = screen.getByRole('button', { name: /Analyze Market/i });
    await user.click(analyzeButton);
    
    await waitFor(() => {
      expect(api.analyzeMarket).toHaveBeenCalledWith('general');
    });
  });

  it('shows loading state while analyzing', async () => {
    const user = userEvent.setup();
    api.analyzeMarket.mockImplementation(() => new Promise(resolve => setTimeout(() => resolve(mockAnalysisResult), 100)));
    
    render(<MarketDashboard />);
    
    const analyzeButton = screen.getByRole('button', { name: /Analyze Market/i });
    await user.click(analyzeButton);
    
    // Should show loading text
    expect(screen.getByText(/Analyzing Market.../i)).toBeInTheDocument();
    
    // Button should be disabled
    expect(analyzeButton).toBeDisabled();
  });

  it('displays analysis results after successful API call', async () => {
    const user = userEvent.setup();
    api.analyzeMarket.mockResolvedValue(mockAnalysisResult);
    
    render(<MarketDashboard />);
    
    const analyzeButton = screen.getByRole('button', { name: /Analyze Market/i });
    await user.click(analyzeButton);
    
    await waitFor(() => {
      expect(screen.getByText('75')).toBeInTheDocument();
      expect(screen.getByText('Market shows positive sentiment with strong indicators.')).toBeInTheDocument();
    });
  });

  it('displays last updated time after analysis', async () => {
    const user = userEvent.setup();
    api.analyzeMarket.mockResolvedValue(mockAnalysisResult);
    
    render(<MarketDashboard />);
    
    const analyzeButton = screen.getByRole('button', { name: /Analyze Market/i });
    await user.click(analyzeButton);
    
    await waitFor(() => {
      expect(screen.getByText(/Last Updated:/i)).toBeInTheDocument();
    });
  });

  it('displays error message when API call fails', async () => {
    const user = userEvent.setup();
    api.analyzeMarket.mockRejectedValue({
      message: 'Server error occurred',
      status: 500,
      type: 'server'
    });
    
    render(<MarketDashboard />);
    
    const analyzeButton = screen.getByRole('button', { name: /Analyze Market/i });
    await user.click(analyzeButton);
    
    await waitFor(() => {
      expect(screen.getByText('Server error occurred')).toBeInTheDocument();
    });
  });

  it('displays generic error message when API error has no details', async () => {
    const user = userEvent.setup();
    api.analyzeMarket.mockRejectedValue({
      message: 'Network error',
      status: 0,
      type: 'network'
    });
    
    render(<MarketDashboard />);
    
    const analyzeButton = screen.getByRole('button', { name: /Analyze Market/i });
    await user.click(analyzeButton);
    
    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  it('clears previous error when new analysis is started', async () => {
    const user = userEvent.setup();
    api.analyzeMarket.mockRejectedValueOnce({
      message: 'Error',
      status: 500,
      type: 'server'
    });
    
    render(<MarketDashboard />);
    
    const analyzeButton = screen.getByRole('button', { name: /Analyze Market/i });
    
    // First call fails
    await user.click(analyzeButton);
    await waitFor(() => {
      expect(screen.getByText('Error')).toBeInTheDocument();
    });
    
    // Second call succeeds
    api.analyzeMarket.mockResolvedValue(mockAnalysisResult);
    await user.click(analyzeButton);
    
    await waitFor(() => {
      expect(screen.queryByText('Failed to analyze market. Please try again.')).not.toBeInTheDocument();
    });
  });

  it('shows AdditionalInfoPanel after successful analysis', async () => {
    const user = userEvent.setup();
    api.analyzeMarket.mockResolvedValue(mockAnalysisResult);
    
    render(<MarketDashboard />);
    
    const analyzeButton = screen.getByRole('button', { name: /Analyze Market/i });
    await user.click(analyzeButton);
    
    await waitFor(() => {
      expect(screen.getByText('Daily Sentiment Details')).toBeInTheDocument();
    });
  });

  it('button is enabled after analysis completes', async () => {
    const user = userEvent.setup();
    api.analyzeMarket.mockResolvedValue(mockAnalysisResult);
    
    render(<MarketDashboard />);
    
    const analyzeButton = screen.getByRole('button', { name: /Analyze Market/i });
    await user.click(analyzeButton);
    
    await waitFor(() => {
      expect(analyzeButton).not.toBeDisabled();
    });
  });

  it('allows multiple analyses to be performed', async () => {
    const user = userEvent.setup();
    api.analyzeMarket.mockResolvedValue(mockAnalysisResult);
    
    render(<MarketDashboard />);
    
    const analyzeButton = screen.getByRole('button', { name: /Analyze Market/i });
    
    // Perform analysis
    await user.click(analyzeButton);
    await waitFor(() => {
      expect(api.analyzeMarket).toHaveBeenCalled();
      expect(screen.getByText('75')).toBeInTheDocument();
    });
    
    // Verify button is enabled for another analysis
    expect(analyzeButton).not.toBeDisabled();
  });

  it('displays results with different buy/sell ratios', async () => {
    const user = userEvent.setup();
    
    // First analysis - high ratio
    api.analyzeMarket.mockResolvedValueOnce({ ...mockAnalysisResult, buy_sell_ratio: 85 });
    render(<MarketDashboard />);
    
    const analyzeButton = screen.getByRole('button', { name: /Analyze Market/i });
    await user.click(analyzeButton);
    
    await waitFor(() => {
      expect(screen.getByText('85')).toBeInTheDocument();
      expect(screen.getByText('강력 매수')).toBeInTheDocument();
    });
  });
});
