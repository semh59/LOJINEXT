import { beforeEach, describe, expect, it, vi } from 'vitest'

import axiosInstance from '../axios-instance'
import { tripService } from '../trip-service'

vi.mock('../axios-instance', () => ({
    default: {
        get: vi.fn(),
        post: vi.fn(),
        patch: vi.fn(),
        delete: vi.fn(),
    },
}))

describe('tripService contract', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    it('bulkDelete sends only body contract { sefer_ids }', async () => {
        ;(axiosInstance.post as any).mockResolvedValue({ data: { success_count: 2 } })

        await tripService.bulkDelete([11, 12])

        expect(axiosInstance.post).toHaveBeenCalledWith('/trips/bulk-delete', {
            sefer_ids: [11, 12],
        })
    })

    it('uploadExcel returns canonical upload response fields', async () => {
        const payload = {
            success: true,
            total_rows: 2,
            success_count: 2,
            failed_count: 0,
            errors: [],
        }
        ;(axiosInstance.post as any).mockResolvedValue({ data: payload })

        const result = await tripService.uploadExcel(new File(['a'], 'trips.xlsx'))

        expect(result).toEqual(payload)
    })

    it('getFuelPerformance passes cleaned filters and returns API payload', async () => {
        const payload = {
            kpis: { mae: 1, rmse: 2, total_compared: 3, high_deviation_ratio: 4 },
            trend: [],
            distribution: {
                good: 0,
                warning: 0,
                error: 0,
                good_pct: 0,
                warning_pct: 0,
                error_pct: 0,
            },
            outliers: [],
            low_data: true,
        }
        ;(axiosInstance.get as any).mockResolvedValue({ data: payload })

        const result = await tripService.getFuelPerformance({
            durum: '',
            baslangic_tarih: '2026-01-01',
            bitis_tarih: '2026-01-31',
        })

        expect(axiosInstance.get).toHaveBeenCalledWith('/trips/analytics/fuel-performance', {
            params: {
                baslangic_tarih: '2026-01-01',
                bitis_tarih: '2026-01-31',
            },
        })
        expect(result).toEqual(payload)
    })

    it('getTimeline parses both wrapped and direct array payloads', async () => {
        const wrapped = [{ id: 1, tip: 'UPDATE' }]
        ;(axiosInstance.get as any).mockResolvedValueOnce({ data: { items: wrapped } })

        const wrappedResult = await tripService.getTimeline(7)
        expect(wrappedResult).toEqual(wrapped)

        const direct = [{ id: 2, tip: 'CREATE' }]
        ;(axiosInstance.get as any).mockResolvedValueOnce({ data: direct })

        const directResult = await tripService.getTimeline(7)
        expect(directResult).toEqual(direct)
    })
})
