import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { FuelTable } from '../FuelTable'
import { FuelRecord } from '../../../types'

const mockRecords: FuelRecord[] = [
    {
        id: 1,
        tarih: '2026-01-25',
        arac_id: 1,
        plaka: '34ABC123',
        istasyon: 'Shell Maslak',
        litre: 450,
        birim_fiyat: 42.50,
        toplam_tutar: 19125,
        km_sayac: 45000,
        depo_durumu: 'Doldu',
        durum: 'Bekliyor'
    }
]

describe('FuelTable', () => {
    it('renders loading state', () => {
        render(<FuelTable records={[]} loading={true} onEdit={() => { }} onDelete={() => { }} />)
        expect(screen.getByText(/Yükleniyor/i)).toBeInTheDocument()
    })

    it('renders empty state', () => {
        render(<FuelTable records={[]} loading={false} onEdit={() => { }} onDelete={() => { }} />)
        expect(screen.getByText(/Kayıt bulunamadı/i)).toBeInTheDocument()
    })

    it('renders records correctly', () => {
        render(<FuelTable records={mockRecords} loading={false} onEdit={() => { }} onDelete={() => { }} />)
        expect(screen.getByText('34ABC123')).toBeInTheDocument()
        expect(screen.getByText('Shell Maslak')).toBeInTheDocument()
        expect(screen.getByText('450 L')).toBeInTheDocument()
        expect(screen.getByText('Doldu')).toBeInTheDocument()
    })

    it('calls onEdit when edit button clicked', () => {
        const handleEdit = vi.fn()
        render(<FuelTable records={mockRecords} loading={false} onEdit={handleEdit} onDelete={() => { }} />)

        const buttons = screen.getAllByRole('button')
        fireEvent.click(buttons[0])

        expect(handleEdit).toHaveBeenCalledTimes(1)
        expect(handleEdit).toHaveBeenCalledWith(mockRecords[0])
    })

    it('calls onDelete when delete button clicked', () => {
        const handleDelete = vi.fn()
        render(<FuelTable records={mockRecords} loading={false} onEdit={() => { }} onDelete={handleDelete} />)

        const buttons = screen.getAllByRole('button')
        fireEvent.click(buttons[1])

        expect(handleDelete).toHaveBeenCalledTimes(1)
        expect(handleDelete).toHaveBeenCalledWith(mockRecords[0])
    })
})
