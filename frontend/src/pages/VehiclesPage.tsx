import { useState, useEffect, useCallback } from 'react'

import { MainLayout } from '../components/layout/MainLayout'
import { VehicleTable } from '../components/vehicles/VehicleTable'
import { VehicleGridView } from '../components/vehicles/VehicleGridView'
import { VehicleModal } from '../components/vehicles/VehicleModal'
import { VehicleUploadModal } from '../components/vehicles/VehicleUploadModal'
import { VehicleDetailModal } from '../components/vehicles/VehicleDetailModal'
import { VehicleDeleteModal } from '../components/vehicles/VehicleDeleteModal'
import { vehiclesApi } from '../services/api'
import { Vehicle } from '../types'
import { Plus, Search, Upload, Download, List, LayoutGrid, Filter, ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { DropdownMenu } from '../components/ui/DropdownMenu'
import { useNotify } from '../context/NotificationContext'
import { Input } from '../components/ui/Input'
import { Toggle } from '../components/ui/Toggle'

const ITEMS_PER_PAGE = 24

export default function VehiclesPage() {
    const { notify } = useNotify()

    // Veri state'leri
    const [vehicles, setVehicles] = useState<Vehicle[]>([])
    const [loading, setLoading] = useState(true)
    const [totalCount, setTotalCount] = useState(0)

    // UI Görünüm State'i
    const [viewMode, setViewMode] = useState<'list' | 'grid'>('grid')
    const [isFilterOpen, setIsFilterOpen] = useState(false)

    // Filter state'leri
    const [search, setSearch] = useState('')
    const [showOnlyActive, setShowOnlyActive] = useState(true)
    const [currentPage, setCurrentPage] = useState(1)

    // Gelişmiş Filtreler
    const [filters, setFilters] = useState({
        marka: '',
        model: '',
        min_yil: '',
        max_yil: ''
    })

    // Modal state'leri
    const [isModalOpen, setIsModalOpen] = useState(false)
    const [isUploadModalOpen, setIsUploadModalOpen] = useState(false)
    const [isDetailModalOpen, setIsDetailModalOpen] = useState(false)
    const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)
    const [selectedVehicle, setSelectedVehicle] = useState<Vehicle | null>(null)
    const [detailVehicle, setDetailVehicle] = useState<Vehicle | null>(null)
    const [vehicleToDelete, setVehicleToDelete] = useState<Vehicle | null>(null)



    // Araçları getir
    const fetchVehicles = useCallback(async () => {
        setLoading(true)
        try {
            const data = await vehiclesApi.getAll({
                search: search || undefined,
                aktif_only: showOnlyActive,
                marka: filters.marka || undefined,
                model: filters.model || undefined,
                min_yil: filters.min_yil ? parseInt(filters.min_yil) : undefined,
                max_yil: filters.max_yil ? parseInt(filters.max_yil) : undefined,
                skip: (currentPage - 1) * ITEMS_PER_PAGE,
                limit: ITEMS_PER_PAGE
            })

            if (Array.isArray(data)) {
                setVehicles(data)
                setTotalCount(data.length)
            } else {
                setVehicles(data.items || [])
                setTotalCount(data.total || 0)
            }
        } catch (error) {
            console.error(error)
            notify('error', 'Hata', 'Araçlar yüklenirken bir sorun oluştu.')
        } finally {
            setLoading(false)
        }
    }, [search, showOnlyActive, currentPage, filters, notify])

    // Filtreler değişince fetch et
    useEffect(() => {
        const timer = setTimeout(() => {
            setCurrentPage(1)
            fetchVehicles()
        }, 500)
        return () => clearTimeout(timer)
    }, [search, showOnlyActive, filters])

    // Sayfa değişince fetch et
    useEffect(() => {
        fetchVehicles()
    }, [currentPage])

    // Araç kaydet
    const handleSave = async (data: Partial<Vehicle>) => {
        try {
            if (selectedVehicle?.id) {
                await vehiclesApi.update(selectedVehicle.id, data)
                notify('success', 'Güncellendi', 'Araç bilgileri başarıyla güncellendi.')
            } else {
                await vehiclesApi.create(data as Vehicle)
                notify('success', 'Eklendi', 'Yeni araç başarıyla eklendi.')
            }
            fetchVehicles()
            setIsModalOpen(false)
        } catch (error: any) {
            notify('error', 'Hata', error?.message || 'İşlem sırasında bir hata oluştu.')
            throw error
        }
    }

    // Silme butonuna basılınca
    const handleDeleteClick = (vehicle: Vehicle) => {
        setVehicleToDelete(vehicle)
        setIsDeleteModalOpen(true)
    }

    // Modalda onaylanınca
    const handleConfirmDelete = async () => {
        if (!vehicleToDelete?.id) return

        try {
            await vehiclesApi.delete(vehicleToDelete.id)
            notify('success', 'İşlem Başarılı', vehicleToDelete.aktif
                ? 'Araç pasife alındı.'
                : 'Araç kalıcı olarak silindi.')
            // Listeyi yenile
            await fetchVehicles()
        } catch (error: any) {
            console.error(error)
            notify('error', 'Hata', error.message || 'Araç silinemedi.')
        }
    }



    // Excel export
    const handleExport = async () => {
        try {
            const blob = await vehiclesApi.export({
                search: search || undefined,
                aktif_only: showOnlyActive
            })
            const url = window.URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `araclar_${new Date().toISOString().split('T')[0]}.xlsx`
            a.click()
            notify('success', 'İndirildi', 'Excel dosyası hazır.')
        } catch (error) {
            notify('error', 'Hata', 'Excel dosyası indirilemedi.')
        } finally {
        }
    }

    const openEditModal = (vehicle?: Vehicle) => {
        setSelectedVehicle(vehicle || null)
        setIsModalOpen(true)
    }

    const openDetailModal = (vehicle: Vehicle) => {
        setDetailVehicle(vehicle)
        setIsDetailModalOpen(true)
    }

    const totalPages = Math.ceil(totalCount / ITEMS_PER_PAGE)

    return (
        <MainLayout title="Araçlar" breadcrumb="Sistem / Araçlar">
            <div className="space-y-6">
                {/* Header Actions */}
                <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6">
                    <div>
                        <h1 className="text-4xl font-black text-neutral-900 tracking-tight flex items-center gap-4">
                            Araç Yönetimi
                            <span className="bg-primary/10 text-primary text-sm font-black px-4 py-1 rounded-full uppercase tracking-widest">
                                {totalCount} ARAÇ
                            </span>
                        </h1>
                        <p className="text-neutral-500 font-medium mt-1">
                            Filodaki araçları modern görünüm ve filtrelerle yönetin.
                        </p>
                    </div>

                    <div className="flex flex-wrap items-center gap-3 w-full lg:w-auto">
                        <div className="flex bg-white border border-neutral-200 p-1 rounded-2xl shadow-sm">
                            <button
                                onClick={() => setViewMode('grid')}
                                className={`p-2 rounded-xl transition-all ${viewMode === 'grid' ? 'bg-primary text-white shadow-md' : 'text-neutral-400 hover:text-neutral-600'}`}
                            >
                                <LayoutGrid className="w-5 h-5" />
                            </button>
                            <button
                                onClick={() => setViewMode('list')}
                                className={`p-2 rounded-xl transition-all ${viewMode === 'list' ? 'bg-primary text-white shadow-md' : 'text-neutral-400 hover:text-neutral-600'}`}
                            >
                                <List className="w-5 h-5" />
                            </button>
                        </div>

                        <Button variant="secondary" onClick={() => setIsFilterOpen(!isFilterOpen)}>
                            <Filter className="w-4 h-4 mr-2" />
                            Filtrele
                        </Button>

                        <DropdownMenu
                            trigger={<Button variant="secondary">İşlemler</Button>}
                            items={[
                                {
                                    label: 'Excel Yükle',
                                    icon: <Upload className="w-4 h-4" />,
                                    onClick: () => setIsUploadModalOpen(true)
                                },
                                {
                                    label: 'Excel İndir',
                                    icon: <Download className="w-4 h-4" />,
                                    onClick: handleExport
                                }
                            ]}
                        />

                        <Button onClick={() => openEditModal()}>
                            <Plus className="w-5 h-5 mr-1.5" />
                            Yeni Araç
                        </Button>
                    </div>
                </div>

                {isFilterOpen && (
                    <div className="mb-6 relative z-10">
                        <div className="bg-white border border-neutral-200 rounded-[32px] p-6 shadow-sm grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                            <div className="space-y-2">
                                <label className="text-xs font-black text-neutral-400 uppercase tracking-widest px-1">Marka</label>
                                <Input
                                    placeholder="Örn: Mercedes"
                                    value={filters.marka}
                                    onChange={(e) => setFilters({ ...filters, marka: e.target.value })}
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-xs font-black text-neutral-400 uppercase tracking-widest px-1">Model</label>
                                <Input
                                    placeholder="Örn: Actros"
                                    value={filters.model}
                                    onChange={(e) => setFilters({ ...filters, model: e.target.value })}
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-xs font-black text-neutral-400 uppercase tracking-widest px-1">Min Yıl</label>
                                <Input
                                    type="number"
                                    placeholder="2010"
                                    value={filters.min_yil}
                                    onChange={(e) => setFilters({ ...filters, min_yil: e.target.value })}
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-xs font-black text-neutral-400 uppercase tracking-widest px-1">Max Yıl</label>
                                <Input
                                    type="number"
                                    placeholder="2024"
                                    value={filters.max_yil}
                                    onChange={(e) => setFilters({ ...filters, max_yil: e.target.value })}
                                />
                            </div>
                        </div>
                    </div>
                )}

                {/* Quick Toolbar */}
                <div className="flex items-center gap-4">
                    <div className="relative flex-1 max-w-md">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400" />
                        <Input
                            placeholder="Plaka veya marka ara..."
                            className="pl-12 bg-white rounded-2xl h-12"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                        />
                    </div>
                    <div className="bg-white border border-neutral-200 rounded-2xl px-5 h-12 flex items-center shadow-sm">
                        <Toggle
                            checked={showOnlyActive}
                            onChange={setShowOnlyActive}
                            label="Aktifler"
                            size="sm"
                        />
                    </div>
                </div>

                {/* Main View */}
                <div className="min-h-[400px]">
                    {viewMode === 'grid' ? (
                        <VehicleGridView
                            vehicles={vehicles}
                            loading={loading}
                            onEdit={openEditModal}
                            onDelete={handleDeleteClick}
                            onViewDetail={openDetailModal}
                        />
                    ) : (
                        <VehicleTable
                            vehicles={vehicles}
                            loading={loading}
                            onEdit={openEditModal}
                            onDelete={async (id) => {
                                // Table component id bazlı çalışıyor, objeyi bulmamız lazım
                                const v = vehicles.find(x => x.id === id)
                                if (v) handleDeleteClick(v)
                            }}
                            onViewDetail={openDetailModal}
                        />
                    )}
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                    <div className="flex items-center justify-between pb-10">
                        <p className="text-sm font-medium text-neutral-500">
                            Toplam <span className="font-bold text-neutral-900">{totalCount}</span> araçtan {(currentPage - 1) * ITEMS_PER_PAGE + 1}-{Math.min(currentPage * ITEMS_PER_PAGE, totalCount)} arası gösteriliyor
                        </p>

                        <div className="flex items-center gap-2">
                            <button
                                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                                disabled={currentPage === 1}
                                className="w-10 h-10 flex items-center justify-center rounded-xl bg-white border border-neutral-200 hover:bg-neutral-50 disabled:opacity-30 transition-all shadow-sm"
                            >
                                <ChevronLeft className="w-5 h-5" />
                            </button>

                            <div className="flex items-center gap-1">
                                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                                    const pageNum = i + 1
                                    return (
                                        <button
                                            key={pageNum}
                                            onClick={() => setCurrentPage(pageNum)}
                                            className={`w-10 h-10 rounded-xl text-sm font-black transition-all ${currentPage === pageNum
                                                ? 'bg-primary text-white shadow-lg shadow-primary/20 scale-110'
                                                : 'bg-white border border-neutral-200 text-neutral-600 hover:border-primary/30'
                                                }`}
                                        >
                                            {pageNum}
                                        </button>
                                    )
                                })}
                            </div>

                            <button
                                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                                disabled={currentPage === totalPages}
                                className="w-10 h-10 flex items-center justify-center rounded-xl bg-white border border-neutral-200 hover:bg-neutral-50 disabled:opacity-30 transition-all shadow-sm"
                            >
                                <ChevronRight className="w-5 h-5" />
                            </button>
                        </div>
                    </div>
                )}

                {/* Modals */}
                {isModalOpen && (
                    <VehicleModal
                        isOpen={isModalOpen}
                        onClose={() => setIsModalOpen(false)}
                        onSave={handleSave}
                        vehicle={selectedVehicle}
                    />
                )}

                {isUploadModalOpen && (
                    <VehicleUploadModal
                        isOpen={isUploadModalOpen}
                        onClose={() => setIsUploadModalOpen(false)}
                        onSuccess={() => {
                            fetchVehicles()
                            notify('success', 'Yüklendi', 'Araçlar başarıyla yüklendi.')
                        }}
                    />
                )}

                {isDetailModalOpen && (
                    <VehicleDetailModal
                        isOpen={isDetailModalOpen}
                        onClose={() => setIsDetailModalOpen(false)}
                        vehicle={detailVehicle}
                    />
                )}

                <VehicleDeleteModal
                    isOpen={isDeleteModalOpen}
                    onClose={() => setIsDeleteModalOpen(false)}
                    onConfirm={handleConfirmDelete}
                    vehicle={vehicleToDelete}
                />
            </div>
        </MainLayout>
    )
}
