import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { TripsModule } from '../TripsModule'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import { tripService } from '../../../services/api/trip-service'
import { vehiclesApi, driversApi, locationService, weatherApi } from '../../../services/api'
import { dorseService } from '../../../services/dorseService'
import { preferenceService } from '../../../services/api/preference-service'
import React from 'react'

// Mock dependencies
vi.mock('../../../services/api/trip-service')
vi.mock('../../../services/api')
vi.mock('../../../services/dorseService')
vi.mock('../../../services/api/preference-service')

// Mock toast
vi.mock('sonner', () => ({
    toast: {
        success: vi.fn(),
        error: vi.fn(),
        warning: vi.fn()
    }
}))

// Mock framer-motion to avoid animation issues in tests
vi.mock('framer-motion', () => ({
    motion: {
        div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
        tr: ({ children, ...props }: any) => <tr {...props}>{children}</tr>,
    },
    AnimatePresence: ({ children }: any) => <>{children}</>,
}))

vi.mock('../../../components/auth/RequirePermission', () => ({
    RequirePermission: ({ children }: any) => <>{children}</>,
}))

vi.mock('@tanstack/react-virtual', () => ({
    useVirtualizer: (args: any) => {
        const count = args?.count ?? 0
        return {
            getTotalSize: () => count * 140,
            getVirtualItems: () => Array.from({ length: count }).map((_, index) => ({
                key: `row-${index}`,
                index,
                size: 140,
                start: index * 140,
            })),
        }
    },
}))

import { MemoryRouter } from 'react-router-dom'

const renderWithClient = (ui: React.ReactNode) => {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: {
                retry: false,
            },
        },
    })

    return render(
        <QueryClientProvider client={queryClient}>
            <MemoryRouter>
                {ui}
            </MemoryRouter>
        </QueryClientProvider>
    )
}

describe('TripsModule Resilience Tests', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        vi.mocked(tripService.getStats).mockResolvedValue({
            toplam_sefer: 0,
            toplam_km: 0,
            highway_km: 0,
            total_ascent: 0,
            total_weight: 0,
            avg_highway_pct: 0,
            last_updated: null,
        } as any)
        vi.mocked(tripService.getFuelPerformance).mockResolvedValue({
            kpis: { mae: 0, rmse: 0, total_compared: 0, high_deviation_ratio: 0 },
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
        } as any)
        vi.mocked(vehiclesApi.getAll).mockResolvedValue({ data: [] })
        vi.mocked(driversApi.getAll).mockResolvedValue({ data: [] })
        vi.mocked(locationService.getAll).mockResolvedValue({ items: [], total: 0 } as any)
        vi.mocked(weatherApi.getTripImpact).mockResolvedValue({ fuel_impact_factor: 1 } as any)
        vi.mocked(dorseService.getAll).mockResolvedValue({ data: [] } as any)
        vi.mocked(preferenceService.getPreferences).mockResolvedValue([])
        vi.mocked(preferenceService.savePreference).mockResolvedValue({} as any)
        vi.mocked(preferenceService.deletePreference).mockResolvedValue({} as any)
    })

    it('displays loading skeleton when fetching data', async () => {
        vi.mocked(tripService.getAll).mockImplementation(() => new Promise(() => {}))

        renderWithClient(<TripsModule />)

        await waitFor(() => {
            const loadingElements = document.getElementsByClassName('animate-pulse')
            expect(loadingElements.length).toBeGreaterThan(0)
        })
    })

    it('displays error UI when API fails', async () => {
        vi.mocked(tripService.getAll).mockRejectedValue(new Error('Network Error'))

        renderWithClient(<TripsModule />)

        expect(await screen.findByText(/Veri Yuklenemedi/i)).toBeInTheDocument()
        expect(screen.getByText(/Yeniden Dene/i)).toBeInTheDocument()
    })

    it('displays empty state when no trips returned', async () => {
        vi.mocked(tripService.getAll).mockResolvedValue({
            items: [],
            meta: { total: 0, skip: 0, limit: 100 }
        })

        renderWithClient(<TripsModule />)

        await waitFor(() => {
            expect(screen.getByText(/Henüz Sefer Bulunmuyor/i)).toBeInTheDocument()
            expect(screen.getByText(/Yeni bir sefer girişi yaparak operasyonu başlatın/i)).toBeInTheDocument()
        })
    })

    it('recovers from error when "Yeniden Dene" is clicked', async () => {
        vi.mocked(tripService.getAll).mockRejectedValueOnce(new Error('Fail 1'))

        renderWithClient(<TripsModule />)

        expect(await screen.findByText(/Veri Yuklenemedi/i)).toBeInTheDocument()

        vi.mocked(tripService.getAll).mockResolvedValue({
            items: [],
            meta: { total: 0, skip: 0, limit: 100 }
        })

        fireEvent.click(screen.getByText(/Yeniden Dene/i))

        expect(await screen.findByText(/Henüz Sefer Bulunmuyor/i)).toBeInTheDocument()
    })

    it('renders pagination safely when limit becomes invalid', async () => {
        vi.mocked(tripService.getAll).mockResolvedValue({
            items: [
                {
                    id: 1,
                    tarih: '2026-01-01',
                    saat: '10:00',
                    arac_id: 1,
                    sofor_id: 1,
                    guzergah_id: 1,
                    cikis_yeri: 'A',
                    varis_yeri: 'B',
                    mesafe_km: 100,
                    bos_agirlik_kg: 8000,
                    dolu_agirlik_kg: 18000,
                    net_kg: 10000,
                    ton: 10,
                    durum: 'Tamam',
                    is_real: true,
                },
            ],
            meta: { total: 1, skip: 0, limit: 0 as any },
        } as any)

        renderWithClient(<TripsModule />)

        expect(await screen.findByText(/1 \/ 1/i)).toBeInTheDocument()
    })
})
