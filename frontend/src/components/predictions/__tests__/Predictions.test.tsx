import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { PredictionResultCard } from '../PredictionResultCard'
import { PredictionResult } from '../../../types'

describe('PredictionResultCard', () => {
    it('renders empty state initially', () => {
        render(<PredictionResultCard result={null} />)
        expect(screen.getByText('Henüz Tahmin Yapılmadı')).toBeInTheDocument()
    })

    it('renders basic result with new backend schema', () => {
        const mockResult: PredictionResult = {
            tahmini_tuketim: 28.5,
            model_used: 'linear',
            status: 'success'
        }

        render(<PredictionResultCard result={mockResult} />)
        expect(screen.getByText('28.5')).toBeInTheDocument()
        expect(screen.getByText(/Linear Regression/i)).toBeInTheDocument()
    })

    it('renders result with optional fields', () => {
        const mockResult: PredictionResult = {
            tahmini_tuketim: 32.1,
            model_used: 'xgboost',
            status: 'success',
            guven_araligi: { min: 29.0, max: 35.0 },
            faktorler: [
                { name: 'Yük Miktarı', impact: 12 },
                { name: 'Tırmanış', impact: 8 }
            ],
            tasarruf_onerisi: 'Hız sabitleyin'
        }

        render(<PredictionResultCard result={mockResult} />)
        expect(screen.getByText('32.1')).toBeInTheDocument()
        expect(screen.getByText(/XGBoost Ensemble/i)).toBeInTheDocument()
        expect(screen.getByText('29.0 - 35.0 L')).toBeInTheDocument()
        expect(screen.getByText('Yük Miktarı')).toBeInTheDocument()
        expect(screen.getByText('Hız sabitleyin')).toBeInTheDocument()
    })

    it('calculates fallback confidence interval when not provided', () => {
        const mockResult: PredictionResult = {
            tahmini_tuketim: 30.0,
            model_used: 'linear'
        }

        render(<PredictionResultCard result={mockResult} />)
        // Fallback: min = 30 * 0.9 = 27.0, max = 30 * 1.1 = 33.0
        expect(screen.getByText('27.0 - 33.0 L')).toBeInTheDocument()
    })
})
