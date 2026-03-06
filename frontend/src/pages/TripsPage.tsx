import { PremiumLayout } from '../components/layout/PremiumLayout'
import { TripsModule } from '../features/trips/TripsModule'

export default function TripsPage() {
    return (
        <PremiumLayout title="Sefer Yönetimi" primaryColor="#25d1f4">
            <TripsModule />
        </PremiumLayout>
    )
}
