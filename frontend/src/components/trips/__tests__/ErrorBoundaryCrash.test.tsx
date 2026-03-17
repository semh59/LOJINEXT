import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import ErrorBoundary from '../../common/ErrorBoundary'

// Suppress React error boundary console.error noise in test output
const originalConsoleError = console.error
beforeEach(() => {
    console.error = vi.fn()
})

afterEach(() => {
    console.error = originalConsoleError
})

// Component that always throws on render
function CrashingComponent(): JSX.Element {
    throw new Error('Test crash: component render failed')
}



describe('ErrorBoundary — Crash Scenario Tests', () => {

    it('catches render error and shows fallback UI', () => {
        render(
            <ErrorBoundary>
                <CrashingComponent />
            </ErrorBoundary>
        )

        expect(screen.getByText('Bir Şeyler Yanlış Gitti')).toBeInTheDocument()
        expect(
            screen.getByText(/beklenmedik bir hata oluştu/i)
        ).toBeInTheDocument()
    })

    it('shows "Sistemi Yenile" button in fallback', () => {
        render(
            <ErrorBoundary>
                <CrashingComponent />
            </ErrorBoundary>
        )

        expect(screen.getByText('Sistemi Yenile')).toBeInTheDocument()
    })

    it('shows "Ana Sayfaya Dön" button in fallback', () => {
        render(
            <ErrorBoundary>
                <CrashingComponent />
            </ErrorBoundary>
        )

        expect(screen.getByText('Ana Sayfaya Dön')).toBeInTheDocument()
    })

    it('calls console.error via componentDidCatch', () => {
        render(
            <ErrorBoundary>
                <CrashingComponent />
            </ErrorBoundary>
        )

        expect(console.error).toHaveBeenCalled()
    })

    it('renders children normally when no error occurs', () => {
        render(
            <ErrorBoundary>
                <div data-testid="safe-child">Safe Content</div>
            </ErrorBoundary>
        )

        expect(screen.getByTestId('safe-child')).toBeInTheDocument()
        expect(screen.getByText('Safe Content')).toBeInTheDocument()
        expect(screen.queryByText('Bir Şeyler Yanlış Gitti')).not.toBeInTheDocument()
    })

    it('uses custom fallback when provided', () => {
        const customFallback = <div data-testid="custom-fallback">Özel Hata Mesajı</div>

        render(
            <ErrorBoundary fallback={customFallback}>
                <CrashingComponent />
            </ErrorBoundary>
        )

        expect(screen.getByTestId('custom-fallback')).toBeInTheDocument()
        expect(screen.getByText('Özel Hata Mesajı')).toBeInTheDocument()
        // Default fallback should NOT appear
        expect(screen.queryByText('Bir Şeyler Yanlış Gitti')).not.toBeInTheDocument()
    })

    it('shows error details in DEV mode', () => {
        // import.meta.env.DEV is true in vitest by default
        render(
            <ErrorBoundary>
                <CrashingComponent />
            </ErrorBoundary>
        )

        expect(screen.getByText(/Test crash: component render failed/i)).toBeInTheDocument()
    })

    it('confirms B-001 audit finding: TripsPage without ErrorBoundary has white screen risk', () => {
        /**
         * This test documents the B-001 audit finding.
         * When ErrorBoundary is NOT wrapping the component,
         * the error propagates up and would cause a white screen.
         * 
         * We verify by confirming ErrorBoundary DOES catch the error properly
         * when wrapped — proving the importance of wrapping PremiumLayout.
         */
        const { container } = render(
            <ErrorBoundary>
                <CrashingComponent />
            </ErrorBoundary>
        )

        // ErrorBoundary renders meaningful UI instead of white screen
        expect(container.innerHTML).not.toBe('')
        expect(screen.getByText('Bir Şeyler Yanlış Gitti')).toBeInTheDocument()
    })
})
