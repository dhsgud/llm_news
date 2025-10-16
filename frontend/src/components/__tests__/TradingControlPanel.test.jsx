import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import TradingControlPanel from '../TradingControlPanel';

describe('TradingControlPanel', () => {
  it('renders control panel', () => {
    const mockHandlers = {
      onStart: vi.fn(),
      onStop: vi.fn(),
      onEmergencyStop: vi.fn(),
    };
    
    render(
      <TradingControlPanel
        isActive={false}
        {...mockHandlers}
        isLoading={false}
      />
    );
    
    expect(screen.getByText('제어 패널')).toBeInTheDocument();
    expect(screen.getByText('자동 매매 상태')).toBeInTheDocument();
  });

  it('shows start button when inactive', () => {
    const mockHandlers = {
      onStart: vi.fn(),
      onStop: vi.fn(),
      onEmergencyStop: vi.fn(),
    };
    
    render(
      <TradingControlPanel
        isActive={false}
        {...mockHandlers}
        isLoading={false}
      />
    );
    
    expect(screen.getByText('자동 매매 시작')).toBeInTheDocument();
    expect(screen.queryByText('자동 매매 중지')).not.toBeInTheDocument();
  });

  it('shows stop button when active', () => {
    const mockHandlers = {
      onStart: vi.fn(),
      onStop: vi.fn(),
      onEmergencyStop: vi.fn(),
    };
    
    render(
      <TradingControlPanel
        isActive={true}
        {...mockHandlers}
        isLoading={false}
      />
    );
    
    expect(screen.getByText('자동 매매 중지')).toBeInTheDocument();
    expect(screen.queryByText('자동 매매 시작')).not.toBeInTheDocument();
  });

  it('calls onStart when start button is clicked', () => {
    const mockHandlers = {
      onStart: vi.fn(),
      onStop: vi.fn(),
      onEmergencyStop: vi.fn(),
    };
    
    render(
      <TradingControlPanel
        isActive={false}
        {...mockHandlers}
        isLoading={false}
      />
    );
    
    const startButton = screen.getByText('자동 매매 시작');
    fireEvent.click(startButton);
    
    expect(mockHandlers.onStart).toHaveBeenCalled();
  });

  it('disables emergency stop when inactive', () => {
    const mockHandlers = {
      onStart: vi.fn(),
      onStop: vi.fn(),
      onEmergencyStop: vi.fn(),
    };
    
    render(
      <TradingControlPanel
        isActive={false}
        {...mockHandlers}
        isLoading={false}
      />
    );
    
    const emergencyButton = screen.getByText('긴급 중지');
    expect(emergencyButton).toBeDisabled();
  });
});
