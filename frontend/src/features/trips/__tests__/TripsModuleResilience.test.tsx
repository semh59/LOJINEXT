
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { TripsModule } from '../TripsModule'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import { tripService } from '../../../services/api/trip-service'
import { vehiclesApi, driversApi } from '../../../services/api'
import React from 'react'

// Mock dependencies
vi.mock('../../../services/api/trip-service')
vi.mock('../../../services/api')

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

const renderWithClient = (ui: React.ReactNode) => {
    // Create specific query client for tests with retries off
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

describe('TripsModule Resilience Tests', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        // Default mocks for side-queries
        vi.mocked(vehiclesApi.getAll).mockResolvedValue({ data: [] })
        vi.mocked(driversApi.getAll).mockResolvedValue({ data: [] })
    })

    it('displays loading skeleton when fetching data', async () => {
        // Mock a promise that doesn't resolve immediately
        vi.mocked(tripService.getAll).mockImplementation(() => new Promise(() => {}))

        renderWithClient(<TripsModule />)

        // Check for loading skeletons (TripTable renders 5 div with animate-pulse)
        // In TripsModule, stats might also have skeletons or TripTable has 5 rows
        // TripTable has 5 skeletons.
        
        // Wait a bit to ensure react-query starts fetching
        await waitFor(() => {
             // We can check if TripTable is rendering the loading state
             // The TripTable loading state has 5 divs
             const loadingElements = document.getElementsByClassName('animate-pulse')
             expect(loadingElements.length).toBeGreaterThan(0)
        })
    })

    it('displays error UI when API fails', async () => {
        // Mock API failure
        vi.mocked(tripService.getAll).mockRejectedValue(new Error('Network Error'))

        renderWithClient(<TripsModule />)

        // TripsModule.tsx renders "Veri Yüklenemedi" on isError
        expect(await screen.findByText(/Veri Yüklenemedi/i)).toBeInTheDocument()
        expect(screen.getByText(/Yeniden Dene/i)).toBeInTheDocument()
    })

    it('displays empty state when no trips returned', async () => {
        // Mock empty list
        vi.mocked(tripService.getAll).mockResolvedValue({ items: [], meta: { total: 0, skip: 0, limit: 100 } })

        renderWithClient(<TripsModule />)

        // Wait for data to load
        await waitFor(() => {
            expect(screen.getByText(/Kayıt Bulunamadı/i)).toBeInTheDocument()
            expect(screen.getByText(/Belirlediğiniz filtrelere uygun sefer kaydı bulunuyor/i)).toBeInTheDocument()
        })
    })

    it('recovers from error when "Yeniden Dene" is clicked', async () => {
        // 1. Fail first
        vi.mocked(tripService.getAll).mockRejectedValueOnce(new Error('Fail 1'))
        
        renderWithClient(<TripsModule />)

        expect(await screen.findByText(/Veri Yüklenemedi/i)).toBeInTheDocument()

        // 2. Succeed next
        const mockTrips = [{ id: 1, plaka: '34RECOVER', durum: 'Tamam' } as any];
        vi.mocked(tripService.getAll).mockResolvedValue({ items: mockTrips, meta: { total: 1, skip: 0, limit: 100 } })

        // Click retry
        const retryBtn = screen.getByText(/Yeniden Dene/i)
        fireEvent.click(retryBtn)

        // Should eventually show the data
        expect(await screen.findByText('34RECOVER')).toBeInTheDocument()
    })
})
