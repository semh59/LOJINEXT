import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { ReportCards } from '../ReportCards'

describe('ReportCards', () => {
    it('renders all cards', () => {
        render(<ReportCards onDownload={vi.fn()} />)
        expect(screen.getByText('Filo Özeti')).toBeInTheDocument()
        expect(screen.getByText('Araç Detay Raporu')).toBeInTheDocument()
    })

    it('calls onDownload when clicked', () => {
        const handleDownload = vi.fn()
        render(<ReportCards onDownload={handleDownload} />)
        const buttons = screen.getAllByText('PDF İndir')
        fireEvent.click(buttons[0])
        expect(handleDownload).toHaveBeenCalledWith('fleet_summary')
    })
})
