
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
        vi.mocked(tripService.getAll).mockResolvedValue([])
        vi.mocked(vehiclesApi.getAll).mockResolvedValue({ data: [{ id: 1, plaka: '34ABC123', marka: 'Test', model: 'X' }] })
        vi.mocked(driversApi.getAll).mockResolvedValue({ data: [{ id: 1, ad_soyad: 'Test Sofor' }] })
    })

    it('renders the trips page layout correctly', async () => {
        renderWithClient(<TripsModule />)

        expect(screen.getByPlaceholderText(/Plaka, şoför veya şehir ara/i)).toBeInTheDocument()
        expect(screen.getByText('Yeni Sefer')).toBeInTheDocument()
        expect(screen.getByText('Excel')).toBeInTheDocument()
    })

    it('opens modal when clicking "Yeni Sefer"', async () => {
        const user = userEvent.setup()
        renderWithClient(<TripsModule />)

        const btn = screen.getByText('Yeni Sefer')
        await user.click(btn)

        expect(await screen.findByRole('dialog')).toBeInTheDocument()
        expect(screen.getByText('Yeni Sefer Girişi')).toBeInTheDocument()
    })

    it('populates vehicle and driver selects in modal', async () => {
        renderWithClient(<TripsModule />)

        fireEvent.click(screen.getByText('Yeni Sefer'))

        await waitFor(() => {
            expect(screen.getByText('34ABC123 - Test X')).toBeInTheDocument()
            expect(screen.getByText('Test Sofor')).toBeInTheDocument()
        })
    })

    it('shows validation error for invalid form submission', async () => {
        renderWithClient(<TripsModule />)

        fireEvent.click(screen.getByText('Yeni Sefer'))
        const saveBtn = await screen.findByText('Seferi Oluştur')

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
        vi.mocked(tripService.getAll).mockResolvedValue(mockTrips)

        renderWithClient(<TripsModule />)

        await waitFor(() => {
            expect(tripService.getAll).toHaveBeenCalled()
        })

        expect(await screen.findByText('34ABC123')).toBeInTheDocument()
        expect(screen.getByText('Ahmet')).toBeInTheDocument()
        expect(screen.getByText('450 km')).toBeInTheDocument()
    })
})
