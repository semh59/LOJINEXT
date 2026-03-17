import { render, screen, fireEvent, waitFor } from '../../../test/test-utils'
import userEvent from '@testing-library/user-event'
import { TripsModule } from '../TripsModule'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import { tripService } from '../../../services/api/trip-service'
import { vehiclesApi, driversApi, locationService, weatherApi } from '../../../services/api'
import { dorseService } from '../../../services/dorseService'
import { preferenceService } from '../../../services/api/preference-service'


vi.mock('../../../services/api/trip-service')
vi.mock('../../../services/api')
vi.mock('../../../services/dorseService')
vi.mock('../../../services/api/preference-service')

vi.mock('../../../components/ui/Modal', () => ({
    Modal: ({ children, isOpen, title }: any) => isOpen ? (
        <div role="dialog" aria-label={title || 'modal'}>
            <h2>{title}</h2>
            {children}
        </div>
    ) : null
}))

vi.mock('sonner', () => ({
    toast: {
        success: vi.fn(),
        error: vi.fn(),
        warning: vi.fn()
    }
}))

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

describe('TripsModule Integration Tests', () => {
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
        vi.mocked(tripService.getAll).mockResolvedValue({ items: [], meta: { total: 0, skip: 0, limit: 100 } })
        vi.mocked(vehiclesApi.getAll).mockResolvedValue({ data: [{ id: 1, plaka: '34ABC123', marka: 'Test', model: 'X' }] })
        vi.mocked(driversApi.getAll).mockResolvedValue({ data: [{ id: 1, ad_soyad: 'Test Sofor' }] })
        vi.mocked(locationService.getAll).mockResolvedValue({ items: [], total: 0 } as any)
        vi.mocked(weatherApi.getTripImpact).mockResolvedValue({ fuel_impact_factor: 1 } as any)
        vi.mocked(dorseService.getAll).mockResolvedValue({ data: [] } as any)
        vi.mocked(preferenceService.getPreferences).mockResolvedValue([])
        vi.mocked(preferenceService.savePreference).mockResolvedValue({} as any)
        vi.mocked(preferenceService.deletePreference).mockResolvedValue({} as any)
    })

    it('renders core header actions', async () => {
        render(<TripsModule />)

        expect(await screen.findByRole('heading', { level: 1, name: /SEFER YÖNETİMİ/i })).toBeInTheDocument()
        expect(screen.getByText(/Yakit Performansi/i)).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /Yeni Sefer Oluştur/i })).toBeInTheDocument()
    })

    it('opens modal when clicking create button', async () => {
        const user = userEvent.setup()
        render(<TripsModule />)

        const createBtn = await screen.findByRole('button', { name: /Yeni Sefer Oluştur/i })
        await user.click(createBtn)

        expect(await screen.findByRole('dialog', { name: /Yeni Sefer/i })).toBeInTheDocument()
    })

    it('calls trip list service on mount', async () => {
        render(<TripsModule />)

        await waitFor(() => {
            expect(tripService.getAll).toHaveBeenCalled()
        })
    })

    it('shows error panel when list request fails', async () => {
        vi.mocked(tripService.getAll).mockRejectedValueOnce({ response: { status: 500 } })
        render(<TripsModule />)

        expect(await screen.findByText('Veri Yuklenemedi')).toBeInTheDocument()
        expect(screen.getByText(/Lutfen internet baglantinizi kontrol/i)).toBeInTheDocument()
    })

    it('opens fuel performance panel', async () => {
        render(<TripsModule />)

        const toggle = await screen.findByText(/Yakit Performansi/i)
        fireEvent.click(toggle)

        expect(await screen.findByText(/Paneli Kapat/i)).toBeInTheDocument()
        await waitFor(() => {
            expect(tripService.getFuelPerformance).toHaveBeenCalled()
        })
    })
})
