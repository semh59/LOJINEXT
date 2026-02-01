import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Suspense, lazy } from 'react'
import { AuthProvider } from './context/AuthContext'
import { NotificationProvider } from './context/NotificationContext'
import LoginPage from './pages/LoginPage'
import { PrivateRoute } from './components/auth/PrivateRoute'

// Lazy loaded pages - Code splitting for better performance
const DashboardPage = lazy(() => import('./pages/DashboardPage'))
const TripsPage = lazy(() => import('./pages/TripsPage'))
const VehiclesPage = lazy(() => import('./pages/VehiclesPage'))
const DriversPage = lazy(() => import('./pages/DriversPage'))
const FuelPage = lazy(() => import('./pages/FuelPage'))
const ReportsPage = lazy(() => import('./pages/ReportsPage'))
const SettingsPage = lazy(() => import('./pages/SettingsPage'))
const LocationsPage = lazy(() => import('./pages/LocationsPage'))
const DesignSystemTest = lazy(() => import('./pages/DesignSystemTest'))

// Loading fallback component
function PageLoader() {
    return (
        <div className="min-h-screen flex items-center justify-center bg-neutral-50">
            <div className="flex flex-col items-center gap-4">
                <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                <span className="text-neutral-500 font-medium">Yükleniyor...</span>
            </div>
        </div>
    )
}

function App() {
    return (
        <BrowserRouter>
            <NotificationProvider>
                <AuthProvider>
                    <Suspense fallback={<PageLoader />}>
                        <Routes>
                            <Route path="/login" element={<LoginPage />} />
                            <Route path="/design-system" element={<DesignSystemTest />} />

                            <Route element={<PrivateRoute />}>
                                <Route path="/dashboard" element={<DashboardPage />} />
                                <Route path="/trips" element={<TripsPage />} />
                                <Route path="/fuel" element={<FuelPage />} />
                                <Route path="/vehicles" element={<VehiclesPage />} />
                                <Route path="/drivers" element={<DriversPage />} />
                                <Route path="/locations" element={<LocationsPage />} />
                                <Route path="/reports" element={<ReportsPage />} />
                                <Route path="/settings" element={<SettingsPage />} />
                                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                            </Route>
                        </Routes>
                    </Suspense>
                </AuthProvider>
            </NotificationProvider>
        </BrowserRouter>
    )
}

export default App
