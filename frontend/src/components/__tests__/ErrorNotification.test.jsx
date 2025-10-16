import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ErrorNotification from '../ErrorNotification';

describe('ErrorNotification Component', () => {
  afterEach(() => {
    vi.clearAllTimers();
  });

  it('should not render when error is null', () => {
    const { container } = render(<ErrorNotification error={null} />);
    expect(container.firstChild).toBeNull();
  });

  it('should render error message', () => {
    const error = {
      message: 'Test error message',
      status: 500,
      type: 'server',
    };

    render(<ErrorNotification error={error} />);
    expect(screen.getByText('Test error message')).toBeInTheDocument();
    expect(screen.getByText('Error Code: 500')).toBeInTheDocument();
  });

  it('should render network error with appropriate styling', () => {
    const error = {
      message: 'Network error',
      status: 0,
      type: 'network',
    };

    const { container } = render(<ErrorNotification error={error} />);
    expect(screen.getByText('Network error')).toBeInTheDocument();
    expect(container.querySelector('.bg-orange-50')).toBeInTheDocument();
  });

  it('should render server error with appropriate styling', () => {
    const error = {
      message: 'Server error',
      status: 500,
      type: 'server',
    };

    const { container } = render(<ErrorNotification error={error} />);
    expect(screen.getByText('Server error')).toBeInTheDocument();
    expect(container.querySelector('.bg-red-50')).toBeInTheDocument();
  });

  it('should call onDismiss when dismiss button is clicked', async () => {
    const user = userEvent.setup();
    const onDismiss = vi.fn();
    const error = {
      message: 'Test error',
      status: 500,
      type: 'server',
    };

    render(<ErrorNotification error={error} onDismiss={onDismiss} autoDismiss={false} />);
    
    const dismissButton = screen.getByRole('button');
    await user.click(dismissButton);

    expect(onDismiss).toHaveBeenCalledTimes(1);
  });

  it('should auto-dismiss after specified time', async () => {
    const onDismiss = vi.fn();
    const error = {
      message: 'Test error',
      status: 500,
      type: 'server',
    };

    render(
      <ErrorNotification 
        error={error} 
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
    const error = {
      message: 'Test error',
      status: 500,
      type: 'server',
    };

    render(
      <ErrorNotification 
        error={error} 
        onDismiss={onDismiss} 
        autoDismiss={false}
      />
    );

    // Wait a bit to ensure it doesn't auto-dismiss
    expect(onDismiss).not.toHaveBeenCalled();
  });

  it('should not show error code when status is 0', () => {
    const error = {
      message: 'Network error',
      status: 0,
      type: 'network',
    };

    render(<ErrorNotification error={error} />);
    expect(screen.queryByText(/Error Code:/)).not.toBeInTheDocument();
  });

  it('should render without dismiss button when onDismiss is not provided', () => {
    const error = {
      message: 'Test error',
      status: 500,
      type: 'server',
    };

    render(<ErrorNotification error={error} />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});
