import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import TradingConfigPanel from '../TradingConfigPanel';

describe('TradingConfigPanel', () => {
  const mockConfig = {
    max_investment: 1000000,
    risk_level: 'medium',
    stop_loss_threshold: 5.0,
    trading_start_time: '09:00',
    trading_end_time: '15:30',
  };

  it('renders configuration form', () => {
    const onSave = vi.fn();
    render(<TradingConfigPanel config={mockConfig} onSave={onSave} isLoading={false} />);
    
    expect(screen.getByText('자동 매매 설정')).toBeInTheDocument();
    expect(screen.getByLabelText(/최대 투자 금액/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/리스크 레벨/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/손절매 임계값/i)).toBeInTheDocument();
  });

  it('displays current config values', () => {
    const onSave = vi.fn();
    render(<TradingConfigPanel config={mockConfig} onSave={onSave} isLoading={false} />);
    
    const maxInvestmentInput = screen.getByLabelText(/최대 투자 금액/i);
    expect(maxInvestmentInput.value).toBe('1000000');
    
    const riskLevelSelect = screen.getByLabelText(/리스크 레벨/i);
    expect(riskLevelSelect.value).toBe('medium');
  });

  it('calls onSave when form is submitted', () => {
    const onSave = vi.fn();
    render(<TradingConfigPanel config={mockConfig} onSave={onSave} isLoading={false} />);
    
    const submitButton = screen.getByText('설정 저장');
    fireEvent.click(submitButton);
    
    expect(onSave).toHaveBeenCalled();
  });

  it('disables submit button when loading', () => {
    const onSave = vi.fn();
    render(<TradingConfigPanel config={mockConfig} onSave={onSave} isLoading={true} />);
    
    const submitButton = screen.getByText('저장 중...');
    expect(submitButton).toBeDisabled();
  });
});
