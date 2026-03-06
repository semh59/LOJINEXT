import { describe, it, expect, vi, beforeEach } from 'vitest';
import { locationService } from '../location-service';
import axiosInstance from '../axios-instance';

// Mock axios instance
vi.mock('../axios-instance', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('locationService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('getAll should fetch locations with filters', async () => {
    const mockData = { items: [], total: 0 };
    (axiosInstance.get as any).mockResolvedValue({ data: mockData });

    const result = await locationService.getAll({ limit: 10, skip: 0 });

    expect(axiosInstance.get).toHaveBeenCalledWith('/locations/', { params: { limit: 10, skip: 0 } });
    expect(result).toEqual(mockData);
  });

  it('create should post new location', async () => {
    const newLoc = { cikis_yeri: 'A', varis_yeri: 'B', mesafe_km: 100 };
    const mockResponse = { id: 1, ...newLoc };
    (axiosInstance.post as any).mockResolvedValue({ data: mockResponse });

    const result = await locationService.create(newLoc as any);

    expect(axiosInstance.post).toHaveBeenCalledWith('/locations/', newLoc);
    expect(result).toEqual(mockResponse);
  });

  it('analyze should trigger route analysis', async () => {
    const mockAnalysis = { success: true, api_mesafe_km: 105 };
    (axiosInstance.post as any).mockResolvedValue({ data: mockAnalysis });

    const result = await locationService.analyze(1);

    expect(axiosInstance.post).toHaveBeenCalledWith('/locations/1/analyze');
    expect(result).toEqual(mockAnalysis);
  });

  it('getRouteInfo should fetch info by coordinates', async () => {
    const coords = { cikis_lat: 41, cikis_lon: 29, varis_lat: 40, varis_lon: 32 };
    const mockInfo = { distance_km: 450 };
    (axiosInstance.get as any).mockResolvedValue({ data: mockInfo });

    const result = await locationService.getRouteInfo(coords);

    expect(axiosInstance.get).toHaveBeenCalledWith('/locations/route-info', { params: coords });
    expect(result).toEqual(mockInfo);
  });
});
