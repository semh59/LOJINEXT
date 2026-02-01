import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { VehicleTable } from '../VehicleTable'
import { Vehicle } from '../../../types'

const mockVehicles: Vehicle[] = [
    { id: 1, plaka: '34ABC123', marka: 'Ford', model: 'Cargo', yil: 2023, tank_kapasitesi: 600, hedef_tuketim: 30, kapasite: 15000, aktif: true },
    { id: 2, plaka: '06XYZ789', marka: 'Mercedes', model: 'Actros', yil: 2022, tank_kapasitesi: 650, hedef_tuketim: 28, kapasite: 18000, aktif: false },
]

describe('VehicleTable', () => {
    it('renders vehicle list correctly', () => {
        render(
            <VehicleTable
                vehicles={mockVehicles}
                loading={false}
                onEdit={vi.fn()}
                onDelete={vi.fn()}
                onViewDetail={vi.fn()}
            />
        )

        expect(screen.getByText('34ABC123')).toBeInTheDocument()
        expect(screen.getByText('Ford')).toBeInTheDocument()
        expect(screen.getByText('15000 kg')).toBeInTheDocument()
        expect(screen.getByText('Aktif')).toBeInTheDocument()
        expect(screen.getByText('Pasif')).toBeInTheDocument()
    })

    it('shows loading state', () => {
        render(
            <VehicleTable
                vehicles={[]}
                loading={true}
                onEdit={vi.fn()}
                onDelete={vi.fn()}
                onViewDetail={vi.fn()}
            />
        )
        expect(screen.queryByText('Henüz Araç Eklenmemiş')).not.toBeInTheDocument()
    })

    it('shows empty state', () => {
        render(
            <VehicleTable
                vehicles={[]}
                loading={false}
                onEdit={vi.fn()}
                onDelete={vi.fn()}
                onViewDetail={vi.fn()}
            />
        )
        expect(screen.getByText('Henüz Araç Eklenmemiş')).toBeInTheDocument()
    })

    it('calls action handlers', () => {
        const handleEdit = vi.fn()
        const handleDelete = vi.fn()

        render(
            <VehicleTable
                vehicles={mockVehicles}
                loading={false}
                onEdit={handleEdit}
                onDelete={handleDelete}
                onViewDetail={vi.fn()}
            />
        )

        // Find delete button by aria-label (assuming VehicleTable update succeeded/will succeed)
        // If VehicleTable update failed, this test will fail. I should ensure VehicleTable is updated.
        const deleteButtons = screen.getAllByLabelText('Sil')
        fireEvent.click(deleteButtons[0])
        expect(handleDelete).toHaveBeenCalledWith(1)

        const editButtons = screen.getAllByLabelText('Düzenle')
        fireEvent.click(editButtons[1])
        expect(handleEdit).toHaveBeenCalledWith(mockVehicles[1])
    })
})
