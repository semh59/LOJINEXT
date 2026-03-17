import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Suspense, lazy } from 'react'
import { AuthProvider } from './context/AuthContext'
import { NotificationProvider } from './context/NotificationContext'
import LoginPage from './pages/LoginPage'
import { PrivateRoute } from './components/auth/PrivateRoute'
import ErrorBoundary from './components/common/ErrorBoundary'

// Lazy loaded pages - Code splitting for better performance
const TripsPage = lazy(() => import('./pages/TripsPage'))
const FleetPage = lazy(() => import('./pages/FleetPage'))
const FuelPage = lazy(() => import('./pages/FuelPage'))

const ReportsPage = lazy(() => import('./pages/ReportsPage'))
const LocationsPage = lazy(() => import('./pages/LocationsPage'))

const AdminLayout = lazy(() => import('./pages/admin/AdminLayout'))
const OverviewPage = lazy(() => import('./pages/admin/OverviewPage'))
const KonfigurasyonPage = lazy(() => import('./pages/admin/KonfigurasyonPage'))
const KullanicilarPage = lazy(() => import('./pages/admin/KullanicilarPage'))
const MLYonetimPage = lazy(() => import('./pages/admin/MLYonetimPage'))
const BakimPage = lazy(() => import('./pages/admin/BakimPage'))
const VeriYonetimPage = lazy(() => import('./pages/admin/VeriYonetimPage'))
const SistemSaglikPage = lazy(() => import('./pages/admin/SistemSaglikPage'))
const BildirimlerPage = lazy(() => import('./pages/admin/BildirimlerPage'))

// Loading fallback component
function PageLoader() {
    return (
        <div className="min-h-screen flex items-center justify-center bg-bg-base">
            <div className="flex flex-col items-center gap-6">
                <div className="w-10 h-10 border-[3px] border-accent/20 border-t-accent rounded-full animate-spin" />
                <span className="text-secondary font-bold text-xs uppercase tracking-[0.2em] animate-pulse">LojiNext Yükleniyor</span>
            </div>
        </div>
    )
}

function App() {
    return (
        <ErrorBoundary>
            <BrowserRouter>
                <NotificationProvider>
                    <AuthProvider>
                        <Suspense fallback={<PageLoader />}>
                            <Routes>
                                <Route path="/login" element={<LoginPage />} />

                                <Route element={<PrivateRoute />}>
                                    <Route path="/trips" element={<TripsPage />} />
                                    <Route path="/fuel" element={<FuelPage />} />
                                    <Route path="/fleet" element={<FleetPage />} />
                                    <Route path="/vehicles" element={<Navigate to="/fleet?tab=vehicles" replace />} />
                                    <Route path="/drivers" element={<Navigate to="/fleet?tab=drivers" replace />} />
                                    <Route path="/locations" element={<LocationsPage />} />
                                    <Route path="/reports" element={<ReportsPage />} />
                                    <Route path="/settings" element={<Navigate to="/admin" replace />} />
                                    
                                    <Route element={<PrivateRoute requiredPermission="admin:read" />}>
                                        <Route path="/admin" element={<AdminLayout />}>
                                            <Route index element={<OverviewPage />} />
                                            <Route path="konfig" element={<KonfigurasyonPage />} />
                                            <Route path="kullanicilar" element={<KullanicilarPage />} />
                                            <Route path="ml" element={<MLYonetimPage />} />
                                            <Route path="bakim" element={<BakimPage />} />
                                            <Route path="veri" element={<VeriYonetimPage />} />
                                            <Route path="saglik" element={<SistemSaglikPage />} />
                                            <Route path="bildirimler" element={<BildirimlerPage />} />
                                            <Route path="*" element={<div className="p-8 text-center text-secondary">Bu modül henüz geliştirme aşamasındadır.</div>} />
                                        </Route>
                                    </Route>

                                    <Route path="/" element={<Navigate to="/trips" replace />} />
                                    
                                    {/* Redirect legacy routes to trips */}
                                    <Route path="/dashboard" element={<Navigate to="/trips" replace />} />
                                    <Route path="/command-center" element={<Navigate to="/trips" replace />} />
                                    <Route path="/intelligence" element={<Navigate to="/trips" replace />} />
                                    <Route path="/monitoring" element={<Navigate to="/trips" replace />} />
                                    <Route path="/efficiency" element={<Navigate to="/trips" replace />} />
                                    <Route path="/alerts" element={<Navigate to="/trips" replace />} />
                                    <Route path="/users" element={<Navigate to="/trips" replace />} />
                                </Route>
                            </Routes>
                        </Suspense>
                    </AuthProvider>
                </NotificationProvider>
            </BrowserRouter>
        </ErrorBoundary>
    )
}

export default App
