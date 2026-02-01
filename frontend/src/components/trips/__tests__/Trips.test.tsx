import { render, screen, fireEvent } from '@testing-library/react'
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
    tripsApi: {
        getAll: vi.fn(),
        create: vi.fn()
    }
}))

describe('NewTripStepper', () => {
    it('navigates through steps', async () => {
        const handleComplete = vi.fn()
        render(<NewTripStepper onComplete={handleComplete} onCancel={vi.fn()} />)

        // Step 1: Vehicle
        // Use findByText which waits automatically (default 1000ms)
        const vehicle = await screen.findByText('34ABC123')
        fireEvent.click(vehicle)

        const nextBtn = screen.getByRole('button', { name: /Devam Et/i })
        // Check if button is enabled
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

        const input1 = screen.getByPlaceholderText('İstanbul Depo')
        fireEvent.change(input1, { target: { value: 'Ist' } })

        const input2 = screen.getByPlaceholderText('Ankara Lojistik')
        fireEvent.change(input2, { target: { value: 'Ank' } })

        const submitBtn = screen.getByRole('button', { name: /Seferi Oluştur/i })
        expect(submitBtn).toBeEnabled()
        fireEvent.click(submitBtn)

        expect(handleComplete).toHaveBeenCalled()
    })
})
