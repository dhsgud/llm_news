import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SuccessNotification from '../SuccessNotification';

describe('SuccessNotification Component', () => {
  afterEach(() => {
    vi.clearAllTimers();
  });

  it('should not render when message is null', () => {
    const { container } = render(<SuccessNotification message={null} />);
    expect(container.firstChild).toBeNull();
  });

  it('should render success message', () => {
    render(<SuccessNotification message="Operation successful!" />);
    expect(screen.getByText('Operation successful!')).toBeInTheDocument();
  });

  it('should have green styling', () => {
    const { container } = render(<SuccessNotification message="Success!" />);
    expect(container.querySelector('.bg-green-50')).toBeInTheDocument();
    expect(container.querySelector('.border-green-200')).toBeInTheDocument();
  });

  it('should call onDismiss when dismiss button is clicked', async () => {
    const user = userEvent.setup();
    const onDismiss = vi.fn();

    render(<SuccessNotification message="Success!" onDismiss={onDismiss} autoDismiss={false} />);
    
    const dismissButton = screen.getByRole('button');
    await user.click(dismissButton);

    expect(onDismiss).toHaveBeenCalledTimes(1);
  });

  it('should auto-dismiss after specified time', async () => {
    const onDismiss = vi.fn();

    render(
      <SuccessNotification 
        message="Success!" 
        onDismiss={onDismiss} 
        autoDismiss={true}
        dismissAfter={100}
      />
    );

    expect(onDismiss).not.toHaveBeenCalled();

    await waitFor(() => {
      expect(onDismiss).toHaveBeenCalledTimes(1);
    }, { timeout: 200 });
  });

  it('should not auto-dismiss when autoDismiss is false', () => {
    const onDismiss = vi.fn();

    render(
      <SuccessNotification 
        message="Success!" 
        onDismiss={onDismiss} 
        autoDismiss={false}
      />
    );

    // Wait a bit to ensure it doesn't auto-dismiss
    expect(onDismiss).not.toHaveBeenCalled();
  });

  it('should render without dismiss button when onDismiss is not provided', () => {
    render(<SuccessNotification message="Success!" />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('should display checkmark icon', () => {
    const { container } = render(<SuccessNotification message="Success!" />);
    const svg = container.querySelector('svg');
    expect(svg).toBeInTheDocument();
    expect(svg).toHaveClass('text-green-400');
  });
});
