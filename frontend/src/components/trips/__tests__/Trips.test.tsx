import { render, screen, fireEvent, waitFor } from '../../../test/test-utils'
import { describe, it, expect, vi } from 'vitest'
import { NewTripStepper } from '../NewTripStepper'

// Mock API
vi.mock('../../../services/api', () => ({
    vehiclesApi: {
        getAll: vi.fn().mockResolvedValue([
            { id: 1, plaka: '34ABC123', marka: 'Ford', model: 'Cargo' }
        ])
    },
    driversApi: {
        getAll: vi.fn().mockResolvedValue([
            { id: 1, ad_soyad: 'Ali Veli', ehliyet_sinifi: 'E', score: 90 }
        ])
    },
    locationService: {
        getAll: vi.fn().mockResolvedValue({
            items: [
                { id: 1, cikis_yeri: 'İstanbul', varis_yeri: 'Ankara', mesafe_km: 450 }
            ],
            total: 1
        }),
        searchByRoute: vi.fn().mockResolvedValue({ found: false })
    },
    tripsApi: {
        getAll: vi.fn(),
        create: vi.fn()
    },
    weatherApi: {
        getTripImpact: vi.fn().mockResolvedValue({ fuel_impact_factor: 1.0 })
    }
}))

describe('NewTripStepper', () => {
    it('navigates through steps', async () => {
        const handleComplete = vi.fn()
        render(<NewTripStepper onComplete={handleComplete} onCancel={vi.fn()} />)

        // Step 1: Vehicle
        const vehicle = await screen.findByText('34ABC123')
        fireEvent.click(vehicle)

        const nextBtn = screen.getByRole('button', { name: /Devam Et/i })
        expect(nextBtn).toBeEnabled()
        fireEvent.click(nextBtn)

        // Step 2: Driver
        const driver = await screen.findByText('Ali Veli')
        fireEvent.click(driver)

        const nextBtn2 = screen.getByRole('button', { name: /Devam Et/i })
        expect(nextBtn2).toBeEnabled()
        fireEvent.click(nextBtn2)

        // Step 3: Route
        await screen.findByText('Rota ve yük detayları')

        const select = screen.getByRole('combobox')
        fireEvent.change(select, { target: { value: '1' } })

        const submitBtn = screen.getByRole('button', { name: /Seferi Oluştur/i })
        expect(submitBtn).toBeEnabled()
        fireEvent.click(submitBtn)

        await waitFor(() => {
            expect(handleComplete).toHaveBeenCalled()
        })
    })
})
