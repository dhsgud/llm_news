import { describe, it, expect, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useApi, useApiMultiple } from '../useApi';

describe('useApi Hook', () => {
  it('should initialize with default values', () => {
    const mockApiFunction = vi.fn();
    const { result } = renderHook(() => useApi(mockApiFunction));

    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(typeof result.current.execute).toBe('function');
    expect(typeof result.current.reset).toBe('function');
  });

  it('should handle successful API call', async () => {
    const mockData = { id: 1, name: 'Test' };
    const mockApiFunction = vi.fn().mockResolvedValue(mockData);
    
    const { result } = renderHook(() => useApi(mockApiFunction));

    await act(async () => {
      await result.current.execute('param1', 'param2');
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
      expect(result.current.data).toEqual(mockData);
      expect(result.current.error).toBeNull();
      expect(mockApiFunction).toHaveBeenCalledWith('param1', 'param2');
    });
  });

  it('should handle API call error', async () => {
    const mockError = new Error('API Error');
    const mockApiFunction = vi.fn().mockRejectedValue(mockError);
    
    const { result } = renderHook(() => useApi(mockApiFunction));

    await act(async () => {
      try {
        await result.current.execute();
      } catch (error) {
        // Expected to throw
      }
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
      expect(result.current.data).toBeNull();
      expect(result.current.error).toEqual(mockError);
    });
  });

  it('should set loading state during API call', async () => {
    const mockApiFunction = vi.fn().mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({ data: 'test' }), 100))
    );
    
    const { result } = renderHook(() => useApi(mockApiFunction));

    act(() => {
      result.current.execute();
    });

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
  });

  it('should reset state', async () => {
    const mockData = { id: 1, name: 'Test' };
    const mockApiFunction = vi.fn().mockResolvedValue(mockData);
    
    const { result } = renderHook(() => useApi(mockApiFunction));

    await act(async () => {
      await result.current.execute();
    });

    await waitFor(() => {
      expect(result.current.data).toEqual(mockData);
    });

    act(() => {
      result.current.reset();
    });

    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.loading).toBe(false);
  });
});

describe('useApiMultiple Hook', () => {
  it('should initialize with default values', () => {
    const { result } = renderHook(() => useApiMultiple());

    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(typeof result.current.executeApi).toBe('function');
    expect(typeof result.current.clearError).toBe('function');
  });

  it('should handle successful API call', async () => {
    const mockData = { id: 1, name: 'Test' };
    const mockApiFunction = vi.fn().mockResolvedValue(mockData);
    
    const { result } = renderHook(() => useApiMultiple());

    let returnedData;
    await act(async () => {
      returnedData = await result.current.executeApi(mockApiFunction, 'param1');
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(returnedData).toEqual(mockData);
      expect(mockApiFunction).toHaveBeenCalledWith('param1');
    });
  });

  it('should handle API call error', async () => {
    const mockError = new Error('API Error');
    const mockApiFunction = vi.fn().mockRejectedValue(mockError);
    
    const { result } = renderHook(() => useApiMultiple());

    await act(async () => {
      try {
        await result.current.executeApi(mockApiFunction);
      } catch (error) {
        // Expected to throw
      }
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toEqual(mockError);
    });
  });

  it('should clear error', async () => {
    const mockError = new Error('API Error');
    const mockApiFunction = vi.fn().mockRejectedValue(mockError);
    
    const { result } = renderHook(() => useApiMultiple());

    await act(async () => {
      try {
        await result.current.executeApi(mockApiFunction);
      } catch (error) {
        // Expected to throw
      }
    });

    await waitFor(() => {
      expect(result.current.error).toEqual(mockError);
    });

    act(() => {
      result.current.clearError();
    });

    expect(result.current.error).toBeNull();
  });

  it('should handle multiple sequential API calls', async () => {
    const mockData1 = { id: 1 };
    const mockData2 = { id: 2 };
    const mockApiFunction1 = vi.fn().mockResolvedValue(mockData1);
    const mockApiFunction2 = vi.fn().mockResolvedValue(mockData2);
    
    const { result } = renderHook(() => useApiMultiple());

    let data1, data2;
    await act(async () => {
      data1 = await result.current.executeApi(mockApiFunction1);
      data2 = await result.current.executeApi(mockApiFunction2);
    });

    expect(data1).toEqual(mockData1);
    expect(data2).toEqual(mockData2);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });
});
