import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AdditionalInfoPanel from '../AdditionalInfoPanel';
import * as api from '../../services/api';

// Mock the API module
vi.mock('../../services/api', () => ({
  getDailySentiment: vi.fn(),
}));

describe('AdditionalInfoPanel Component', () => {
  const mockDailyData = [
    { date: '2025-10-01', score: 0.5 },
    { date: '2025-10-02', score: -1.5 },
    { date: '2025-10-03', score: 0.0 },
    { date: '2025-10-04', score: 1.0 },
    { date: '2025-10-05', score: -0.8 },
    { date: '2025-10-06', score: 0.3 },
    { date: '2025-10-07', score: 0.7 },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the toggle button', () => {
    render(<AdditionalInfoPanel />);
    
    expect(screen.getByText('Daily Sentiment Details')).toBeInTheDocument();
  });

  it('panel is initially closed', () => {
    render(<AdditionalInfoPanel />);
    
    // Table headers should not be visible when closed
    expect(screen.queryByText('Date')).not.toBeInTheDocument();
    expect(screen.queryByText('Score')).not.toBeInTheDocument();
  });

  it('opens panel when toggle button is clicked', async () => {
    const user = userEvent.setup();
    api.getDailySentiment.mockResolvedValue(mockDailyData);
    
    render(<AdditionalInfoPanel />);
    
    const toggleButton = screen.getByText('Daily Sentiment Details');
    await user.click(toggleButton);
    
    // Should show loading state first
    await waitFor(() => {
      expect(screen.getByText('Date')).toBeInTheDocument();
    });
  });

  it('closes panel when toggle button is clicked again', async () => {
    const user = userEvent.setup();
    api.getDailySentiment.mockResolvedValue(mockDailyData);
    
    render(<AdditionalInfoPanel />);
    
    const toggleButton = screen.getByText('Daily Sentiment Details');
    
    // Open panel
    await user.click(toggleButton);
    await waitFor(() => {
      expect(screen.getByText('Date')).toBeInTheDocument();
    });
    
    // Close panel
    await user.click(toggleButton);
    await waitFor(() => {
      expect(screen.queryByText('Date')).not.toBeInTheDocument();
    });
  });

  it('fetches and displays daily sentiment data', async () => {
    const user = userEvent.setup();
    api.getDailySentiment.mockResolvedValue(mockDailyData);
    
    render(<AdditionalInfoPanel />);
    
    const toggleButton = screen.getByText('Daily Sentiment Details');
    await user.click(toggleButton);
    
    await waitFor(() => {
      expect(api.getDailySentiment).toHaveBeenCalledWith(7);
      expect(screen.getByText('Date')).toBeInTheDocument();
      expect(screen.getByText('Score')).toBeInTheDocument();
      expect(screen.getByText('Sentiment')).toBeInTheDocument();
    });
  });

  it('displays loading state while fetching data', async () => {
    const user = userEvent.setup();
    api.getDailySentiment.mockImplementation(() => new Promise(resolve => setTimeout(() => resolve(mockDailyData), 100)));
    
    render(<AdditionalInfoPanel />);
    
    const toggleButton = screen.getByText('Daily Sentiment Details');
    await user.click(toggleButton);
    
    // Should show loading spinner
    const spinner = document.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('displays error message when API call fails', async () => {
    const user = userEvent.setup();
    api.getDailySentiment.mockRejectedValue(new Error('API Error'));
    
    render(<AdditionalInfoPanel />);
    
    const toggleButton = screen.getByText('Daily Sentiment Details');
    await user.click(toggleButton);
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load daily sentiment data')).toBeInTheDocument();
    });
  });

  it('displays sentiment data in table format', async () => {
    const user = userEvent.setup();
    api.getDailySentiment.mockResolvedValue(mockDailyData);
    
    render(<AdditionalInfoPanel />);
    
    const toggleButton = screen.getByText('Daily Sentiment Details');
    await user.click(toggleButton);
    
    await waitFor(() => {
      // Check for positive sentiment
      expect(screen.getByText('0.50')).toBeInTheDocument();
      expect(screen.getByText('-1.50')).toBeInTheDocument();
      expect(screen.getByText('0.00')).toBeInTheDocument();
    });
  });

  it('displays correct sentiment labels', async () => {
    const user = userEvent.setup();
    api.getDailySentiment.mockResolvedValue(mockDailyData);
    
    render(<AdditionalInfoPanel />);
    
    const toggleButton = screen.getByText('Daily Sentiment Details');
    await user.click(toggleButton);
    
    await waitFor(() => {
      const positiveLabels = screen.getAllByText('Positive');
      const negativeLabels = screen.getAllByText('Negative');
      const neutralLabels = screen.getAllByText('Neutral');
      
      expect(positiveLabels.length).toBeGreaterThan(0);
      expect(negativeLabels.length).toBeGreaterThan(0);
      expect(neutralLabels.length).toBeGreaterThan(0);
    });
  });

  it('only fetches data once when opened', async () => {
    const user = userEvent.setup();
    api.getDailySentiment.mockResolvedValue(mockDailyData);
    
    render(<AdditionalInfoPanel />);
    
    const toggleButton = screen.getByText('Daily Sentiment Details');
    
    // Open panel
    await user.click(toggleButton);
    await waitFor(() => {
      expect(api.getDailySentiment).toHaveBeenCalledTimes(1);
    });
    
    // Close and reopen
    await user.click(toggleButton);
    await user.click(toggleButton);
    
    // Should still only be called once (data is cached)
    expect(api.getDailySentiment).toHaveBeenCalledTimes(1);
  });

  it('rotates arrow icon when panel is opened', async () => {
    const user = userEvent.setup();
    api.getDailySentiment.mockResolvedValue(mockDailyData);
    
    render(<AdditionalInfoPanel />);
    
    const toggleButton = screen.getByText('Daily Sentiment Details');
    const arrow = toggleButton.parentElement.querySelector('svg');
    
    // Initially not rotated
    expect(arrow).not.toHaveClass('rotate-180');
    
    // Click to open
    await user.click(toggleButton);
    
    // Should be rotated
    await waitFor(() => {
      expect(arrow).toHaveClass('rotate-180');
    });
  });
});
