import { MainLayout } from '../components/layout/MainLayout'
import { TripsModule } from '../features/trips/TripsModule'

export default function TripsPage() {
    return (
        <MainLayout title="Seferler" breadcrumb="Sistem / Sefer Yönetimi">
            <TripsModule />
        </MainLayout>
    )
}
