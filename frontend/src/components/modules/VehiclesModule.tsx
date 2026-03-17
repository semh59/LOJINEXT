import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { VehicleTable } from '../vehicles/VehicleTable'
import { VehicleModal } from '../vehicles/VehicleModal'
import { VehicleDetailModal } from '../vehicles/VehicleDetailModal'
import { VehicleDeleteModal } from '../vehicles/VehicleDeleteModal'
import { VehicleHeader } from '../vehicles/VehicleHeader'
import { VehicleFilters } from '../vehicles/VehicleFilters'
import { vehicleService } from '../../services/api/vehicle-service'
import { Vehicle } from '../../types'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useNotify } from '../../context/NotificationContext'
import { useUrlState } from '../../hooks/use-url-state'

const ITEMS_PER_PAGE = 24

export function VehiclesModule() {
    const { notify } = useNotify()
    const queryClient = useQueryClient()

    // UI Görünüm State'i
    const [isFilterOpen, setIsFilterOpen] = useState(false)

    const [urlState, setUrlState] = useUrlState({
        search: '',
        aktif: true as boolean,
        page: 1,
        marka: '',
        model: '',
        min_yil: '',
        max_yil: ''
    })

    const { 
        search, 
        aktif: showOnlyActive, 
        page: currentPage,
        marka,
        model,
        min_yil,
        max_yil
    } = urlState

    const filters = { marka, model, min_yil, max_yil }

    // Modal state'leri
    const [isModalOpen, setIsModalOpen] = useState(false)
    const [isDetailModalOpen, setIsDetailModalOpen] = useState(false)
    const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)
    const [selectedVehicle, setSelectedVehicle] = useState<Vehicle | null>(null)
    const [detailVehicle, setDetailVehicle] = useState<Vehicle | null>(null)
    const [vehicleToDelete, setVehicleToDelete] = useState<Vehicle | null>(null)

    // React Query: Fetch Vehicles
    const { data, isLoading } = useQuery({
        queryKey: ['vehicles', { search, showOnlyActive, currentPage, filters }],
        queryFn: () => vehicleService.getAll({
            search: search || undefined,
            aktif_only: showOnlyActive,
            marka: filters.marka || undefined,
            model: filters.model || undefined,
            min_yil: filters.min_yil ? parseInt(filters.min_yil) : undefined,
            max_yil: filters.max_yil ? parseInt(filters.max_yil) : undefined,
            skip: (currentPage - 1) * ITEMS_PER_PAGE,
            limit: ITEMS_PER_PAGE
        }),
    })

    const vehicles = Array.isArray(data) ? data : data?.items || []
    const totalCount = Array.isArray(data) ? data.length : data?.total || 0
    const totalPages = Math.ceil(totalCount / ITEMS_PER_PAGE) || 1

    // Mutations
    const handleSave = async (data: Partial<Vehicle>) => {
        try {
            if (selectedVehicle?.id) {
                await vehicleService.update(selectedVehicle.id, data)
                notify('success', 'Güncellendi', 'Araç bilgileri başarıyla güncellendi.')
            } else {
                await vehicleService.create(data as Vehicle)
                notify('success', 'Eklendi', 'Yeni araç başarıyla eklendi.')
            }
            queryClient.invalidateQueries({ queryKey: ['vehicles'] })
            setIsModalOpen(false)
        } catch (error: any) {
            notify('error', 'Hata', error?.message || 'İşlem sırasında bir hata oluştu.')
            throw error
        }
    }

    const handleConfirmDelete = async () => {
        if (!vehicleToDelete?.id) return
        try {
            await vehicleService.delete(vehicleToDelete.id)
            notify('success', 'İşlem Başarılı', 'İşlem tamamlandı.')
            queryClient.invalidateQueries({ queryKey: ['vehicles'] })
        } catch (error: any) {
            notify('error', 'Hata', error.message || 'Araç silinemedi.')
        } finally {
            setIsDeleteModalOpen(false)
        }
    }

    const handleExport = async () => {
        try {
            const blob = await vehicleService.exportExcel({
                search: search || undefined,
                aktif_only: showOnlyActive,
                marka: filters.marka || undefined,
                model: filters.model || undefined,
                min_yil: filters.min_yil ? parseInt(filters.min_yil) : undefined,
                max_yil: filters.max_yil ? parseInt(filters.max_yil) : undefined,
            })
            const url = window.URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `araclar_export_${new Date().toISOString().split('T')[0]}.xlsx`
            document.body.appendChild(a)
            a.click()
            window.URL.revokeObjectURL(url)
            document.body.removeChild(a)
            notify('success', 'Başarılı', 'Excel dosyası hazırlandı.')
        } catch (error) {
            notify('error', 'Hata', 'Dışa aktarma başarısız.')
        }
    }

    const handleDownloadTemplate = async () => {
        try {
            const blob = await vehicleService.downloadTemplate()
            const url = window.URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = 'arac_yukleme_sablonu.xlsx'
            document.body.appendChild(a)
            a.click()
            window.URL.revokeObjectURL(url)
            document.body.removeChild(a)
            notify('success', 'Başarılı', 'Şablon indirildi.')
        } catch (error) {
            notify('error', 'Hata', 'Şablon indirilemedi.')
        }
    }

    const handleImport = async (file: File) => {
        try {
            const res = await vehicleService.uploadExcel(file)
            notify("success", "Başarılı", "Araçlar başarıyla içe aktarıldı.")
            queryClient.invalidateQueries({ queryKey: ['vehicles'] })
            return res
        } catch (error) {
            notify("error", "Hata", "İçe aktarma başarısız.")
            throw error
        }
    }

    const handleEdit = (vehicle: Vehicle) => {
        setSelectedVehicle(vehicle)
        setIsModalOpen(true)
    }

    const handleDelete = (vehicle: Vehicle): void => {
        setVehicleToDelete(vehicle)
        setIsDeleteModalOpen(true)
    }

    const handleViewDetail = (vehicle: Vehicle) => {
        setDetailVehicle(vehicle)
        setIsDetailModalOpen(true)
    }

    return (
        <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-8"
        >
            <VehicleHeader 
                onAdd={() => { setSelectedVehicle(null); setIsModalOpen(true); }}
                onExport={handleExport}
                onDownloadTemplate={handleDownloadTemplate}
                onImport={handleImport as any}
            />

            <VehicleFilters 
                search={search}
                setSearch={(val) => setUrlState({ search: val, page: 1 })}
                showOnlyActive={showOnlyActive}
                setShowOnlyActive={(val) => setUrlState({ aktif: val, page: 1 })}
                isFilterOpen={isFilterOpen}
                setIsFilterOpen={setIsFilterOpen}
                filters={filters}
                setFilters={(newFilters: any) => setUrlState({ ...newFilters, page: 1 })}
            />

            {/* Content Area */}
            <div className="min-h-[400px]">
                {isLoading ? (
                    <div className="flex items-center justify-center pt-20">
                        <div className="w-12 h-12 border-4 border-accent border-t-transparent rounded-full animate-spin" />
                    </div>
                ) : (
                    <VehicleTable
                        vehicles={vehicles}
                        onEdit={handleEdit}
                        onDelete={handleDelete}
                        onViewDetail={handleViewDetail}
                        loading={false}
                    />
                )}
            </div>

            {/* Pagination */}
            {!isLoading && totalPages > 1 && (
                <div className="flex items-center justify-center pt-8">
                    <div className="bg-surface px-2 py-2 rounded-2xl flex items-center gap-1 border border-border shadow-sm">
                        <button
                            onClick={() => setUrlState({ page: Math.max(1, currentPage - 1) })}
                            disabled={currentPage === 1}
                            className="p-2 rounded-xl bg-bg-elevated text-primary border border-border disabled:opacity-30 hover:border-secondary transition-all"
                        >
                            <ChevronLeft className="w-5 h-5" />
                        </button>
                        <span className="px-4 font-bold text-sm text-primary tracking-tight">
                            Sayfa {currentPage} / {totalPages}
                        </span>
                        <button
                            onClick={() => setUrlState({ page: Math.min(totalPages, currentPage + 1) })}
                            disabled={currentPage === totalPages}
                            className="p-2 rounded-xl bg-bg-elevated text-primary border border-border disabled:opacity-30 hover:border-secondary transition-all"
                        >
                            <ChevronRight className="w-5 h-5" />
                        </button>
                    </div>
                </div>
            )}

            {/* Modals */}
            <VehicleModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onSave={handleSave}
                vehicle={selectedVehicle}
            />

            <VehicleDetailModal
                isOpen={isDetailModalOpen}
                onClose={() => setIsDetailModalOpen(false)}
                vehicle={detailVehicle}
            />

            <VehicleDeleteModal
                isOpen={isDeleteModalOpen}
                onClose={() => setIsDeleteModalOpen(false)}
                onConfirm={handleConfirmDelete}
                vehicle={vehicleToDelete}
            />
        </motion.div>
    )
}
