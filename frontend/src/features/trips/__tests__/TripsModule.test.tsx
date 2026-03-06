
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TripsModule } from '../TripsModule'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import { tripService } from '../../../services/api/trip-service'
import { vehiclesApi, driversApi } from '../../../services/api'
import React from 'react'

// Mock dependencies
vi.mock('../../../services/api/trip-service')
vi.mock('../../../services/api')

// Re-mock Modal
vi.mock('../../../components/ui/Modal', () => ({
    Modal: ({ children, isOpen, title }: any) => isOpen ? (
        <div role="dialog" aria-label={title || "modal"}>
            <h2>{title}</h2>
            {children}
        </div>
    ) : null
}))

// Mock toast
vi.mock('sonner', () => ({
    toast: {
        success: vi.fn(),
        error: vi.fn(),
        warning: vi.fn()
    }
}))

// Mock framer-motion
vi.mock('framer-motion', () => ({
    motion: {
        div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
        tr: ({ children, ...props }: any) => <tr {...props}>{children}</tr>,
    },
    AnimatePresence: ({ children }: any) => <>{children}</>,
}))

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
            {ui}
        </QueryClientProvider>
    )
}

describe('TripsModule Integration Tests', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        // Default mocks
        vi.mocked(tripService.getAll).mockResolvedValue({ items: [], meta: { total: 0, skip: 0, limit: 100 } })
        vi.mocked(vehiclesApi.getAll).mockResolvedValue({ data: [{ id: 1, plaka: '34ABC123', marka: 'Test', model: 'X' }] })
        vi.mocked(driversApi.getAll).mockResolvedValue({ data: [{ id: 1, ad_soyad: 'Test Sofor' }] })
    })

    it('renders the trips page layout correctly', async () => {
        renderWithClient(<TripsModule />)

        expect(screen.getByPlaceholderText(/Plaka, şoför veya şehir ara/i)).toBeInTheDocument()
        expect(screen.getByText(/Yeni Sefer Başlat/i)).toBeInTheDocument()
        expect(screen.getByText(/Excel İşlemleri/i)).toBeInTheDocument()
    })

    it('opens modal when clicking "Yeni Sefer Başlat"', async () => {
        const user = userEvent.setup()
        renderWithClient(<TripsModule />)

        const btn = screen.getByText(/Yeni Sefer Başlat/i)
        await user.click(btn)

        expect(await screen.findByRole('dialog')).toBeInTheDocument()
        expect(screen.getByText('Yeni Sefer Girişi')).toBeInTheDocument()
    })

    it('populates vehicle and driver selects in modal', async () => {
        renderWithClient(<TripsModule />)

        fireEvent.click(screen.getByText(/Yeni Sefer Başlat/i))

        await waitFor(() => {
            expect(screen.getByText('34ABC123')).toBeInTheDocument()
            expect(screen.getByText('Test Sofor')).toBeInTheDocument()
        })
    })

    it('shows validation error for invalid form submission', async () => {
        renderWithClient(<TripsModule />)

        fireEvent.click(screen.getByText(/Yeni Sefer Başlat/i))
        const saveBtn = await screen.findByText(/Kaydet/i)

        fireEvent.click(saveBtn)

        await waitFor(() => {
            // Zod validation messages from schema
            expect(screen.getByText(/Araç seçimi gereklidir/i)).toBeInTheDocument()
            expect(screen.getByText(/Şoför seçimi gereklidir/i)).toBeInTheDocument()
        })
    })

    it('renders list of trips from API', async () => {
        const mockTrips = [
            {
                id: 1,
                tarih: '2026-01-01',
                saat: '10:00',
                plaka: '34ABC123',
                sofor_adi: 'Ahmet',
                cikis_yeri: 'Ankara',
                varis_yeri: 'Istanbul',
                mesafe_km: 450,
                durum: 'Tamam'
            }
        ] as any
        vi.mocked(tripService.getAll).mockResolvedValue({ items: mockTrips, meta: { total: mockTrips.length, skip: 0, limit: 100 } })

        renderWithClient(<TripsModule />)

        await waitFor(() => {
            expect(tripService.getAll).toHaveBeenCalled()
        })

        expect(await screen.findByText('34ABC123')).toBeInTheDocument()
        expect(screen.getByText('Ahmet')).toBeInTheDocument()
        expect(screen.getAllByText(/450 km/i)[0]).toBeInTheDocument()
    })

    it('performs bulk delete successfully', async () => {
        const mockTrips = [
            { id: 1, plaka: '34ABC123', sofor_adi: 'Ahmet', tarih: '2026-01-01', durum: 'Tamam' },
            { id: 2, plaka: '34XYZ789', sofor_adi: 'Mehmet', tarih: '2026-01-02', durum: 'Tamam' }
        ] as any
        vi.mocked(tripService.getAll).mockResolvedValue({ items: mockTrips, meta: { total: mockTrips.length, skip: 0, limit: 100 } })
        vi.mocked(tripService.bulkDelete).mockResolvedValue({ status: 'success', deleted: 2, total: 2, errors: [] })

        renderWithClient(<TripsModule />)

        // Wait for rows to render
        await waitFor(() => {
            expect(screen.getByText('34ABC123')).toBeInTheDocument()
        })

        // Select all
        const selectAllCheckbox = screen.getAllByRole('checkbox')[0]
        fireEvent.click(selectAllCheckbox)

        // Bulk action bar should appear
        expect(await screen.findByText(/2 Kayıt Seçildi/i)).toBeInTheDocument()

        // Click delete
        const bulkDeleteBtn = screen.getByText(/Toplu Sil/i)
        
        // Mock confirm
        vi.spyOn(window, 'confirm').mockReturnValue(true)
        
        fireEvent.click(bulkDeleteBtn)

        await waitFor(() => {
            expect(tripService.bulkDelete).toHaveBeenCalledWith([1, 2])
        })
    })
})
