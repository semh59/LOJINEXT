import { PremiumLayout } from '../components/layout/PremiumLayout'
import { TripsModule } from '../features/trips/TripsModule'
import ErrorBoundary from '../components/common/ErrorBoundary'

export default function TripsPage() {
    return (
        <PremiumLayout title="Sefer Yönetimi">
            <ErrorBoundary>
                <TripsModule />
            </ErrorBoundary>
        </PremiumLayout>
    )
}
