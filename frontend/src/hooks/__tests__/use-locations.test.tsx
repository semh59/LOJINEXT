import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useLocations } from '../use-locations';
import { locationService } from '../../services/api/location-service';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';

// Mock the service
vi.mock('../../services/api/location-service', () => ({
  locationService: {
    getAll: vi.fn(),
    create: vi.fn(),
    analyze: vi.fn(),
  },
}));

// Mock toast to avoid errors related to DOM
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const createWrapper = () => {
    const queryClient = new QueryClient({
        defaultOptions: { 
            queries: { retry: false, gcTime: 0 },
            mutations: { retry: false }
        },
    });
    return ({ children }: { children: React.ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
};

describe('useLocations hooks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('useGetLocations should fetch and return locations', async () => {
    const mockData = { items: [{ id: 1, cikis_yeri: 'A', varis_yeri: 'B' }], total: 1 };
    (locationService.getAll as any).mockResolvedValue(mockData);

    // Initial render of main hook
    const { result } = renderHook(() => useLocations({ limit: 10, skip: 0 }), {
      wrapper: createWrapper(),
    });

    // Execute the nested hook
    const { result: getLocResult } = renderHook(() => result.current.useGetLocations(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(getLocResult.current.isSuccess).toBe(true));
    expect(getLocResult.current.data?.items).toHaveLength(1);
  });

  it('useCreateLocation should call service create', async () => {
    const newLoc = { cikis_yeri: 'C', varis_yeri: 'D', mesafe_km: 50 };
    (locationService.create as any).mockResolvedValue({ id: 2, ...newLoc });

    const { result } = renderHook(() => useLocations().useCreateLocation(), {
      wrapper: createWrapper(),
    });

    await result.current.mutateAsync(newLoc as any);
    expect(locationService.create).toHaveBeenCalledWith(newLoc);
  });
});
