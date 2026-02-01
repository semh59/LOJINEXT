import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { DriverCard } from '../DriverCard'
import { Driver } from '../../../types'

const mockDriver: Driver = {
    id: 1,
    ad_soyad: 'Ahmet Yılmaz',
    ehliyet_sinifi: 'E',
    score: 95,
    manual_score: 0,
    aktif: true,
    telefon: '5551234567'
}

describe('DriverCard', () => {
    it('renders driver info correctly', () => {
        render(
            <DriverCard
                driver={mockDriver}
                onEdit={vi.fn()}
                onDelete={vi.fn()}
            />
        )

        expect(screen.getByText('Ahmet Yılmaz')).toBeInTheDocument()
        expect(screen.getByText('E Sınıfı')).toBeInTheDocument()
        expect(screen.getByText('95')).toBeInTheDocument()
        expect(screen.getByText('5551234567')).toBeInTheDocument()
    })

    it('shows active status', () => {
        const { container } = render(
            <DriverCard
                driver={mockDriver}
                onEdit={vi.fn()}
                onDelete={vi.fn()}
            />
        )
        // Check for active indicator (green dot)
        expect(container.querySelector('[title="Aktif"]')).toBeInTheDocument()
    })
})
