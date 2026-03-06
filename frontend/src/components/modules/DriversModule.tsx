import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { DriverModal } from '../drivers/DriverModal'
import { DriverScoreModal } from '../drivers/DriverScoreModal'
import { DriverPerformanceModal } from '../drivers/DriverPerformanceModal'
import { DriverTable } from '../drivers/DriverTable'
import { DriverGrid } from '../drivers/DriverGrid'
import { DriverFilters } from '../drivers/DriverFilters'
import { DriverHeader } from '../drivers/DriverHeader'
import { driverService } from '../../services/api/driver-service'
import { Driver } from '../../types'
import { useNotify } from '../../context/NotificationContext'

// Ehliyet sınıfları
const EHLIYET_OPTIONS = ['', 'B', 'C', 'CE', 'D', 'D1E', 'E', 'G']

export function DriversModule() {
    const { notify } = useNotify()
    const queryClient = useQueryClient()
    
    // Modaller
    const [isModalOpen, setIsModalOpen] = useState(false)
    const [isScoreModalOpen, setIsScoreModalOpen] = useState(false)
    const [isPerformanceModalOpen, setIsPerformanceModalOpen] = useState(false)
    const [selectedDriver, setSelectedDriver] = useState<Driver | null>(null)

    // Görünüm modu
    const [viewMode, setViewMode] = useState<'table' | 'grid'>('grid')

    // Filtreler
    const [search, setSearch] = useState('')
    const [aktifOnly, setAktifOnly] = useState(true)
    const [ehliyetFilter, setEhliyetFilter] = useState('')
    const page = 1
    const limit = 20

    // React Query: Fetch Drivers
    const { data: drivers = [], isLoading } = useQuery({
        queryKey: ['drivers', { page, search, aktifOnly, ehliyetFilter }],
        queryFn: () => driverService.getAll({
            skip: (page - 1) * limit,
            limit: limit,
            search: search || undefined,
            aktif_only: aktifOnly,
            ehliyet_sinifi: ehliyetFilter || undefined,
        }),
    })

    // React Query: Mutations
    const deleteMutation = useMutation({
        mutationFn: (driver: Driver) => driverService.delete(driver.id!),
        onSuccess: (_, driver) => {
            notify('success', 'Başarılı', driver.aktif ? 'Sürücü pasife çekildi.' : 'Sürücü silindi.')
            queryClient.invalidateQueries({ queryKey: ['drivers'] })
        },
        onError: (error: any) => {
            notify('error', 'Hata', error.response?.data?.detail || 'İşlem başarısız.')
        }
    })

    const handleSave = async (data: Partial<Driver>) => {
        try {
            if (selectedDriver?.id) {
                await driverService.update(selectedDriver.id, data)
                notify('success', 'Güncellendi', 'Sürücü bilgileri başarıyla güncellendi.')
            } else {
                await driverService.create(data)
                notify('success', 'Eklendi', 'Yeni sürücü başarıyla eklendi.')
            }
            queryClient.invalidateQueries({ queryKey: ['drivers'] })
            setIsModalOpen(false)
        } catch (error) {
            notify('error', 'Hata', 'İşlem sırasında bir hata oluştu.')
            throw error
        }
    }

    const handleScoreSave = async (score: number) => {
        if (!selectedDriver?.id) return
        try {
            await driverService.updateScore(selectedDriver.id, score)
            notify('success', 'Puan Güncellendi', 'Sürücü puanı başarıyla güncellendi.')
            queryClient.invalidateQueries({ queryKey: ['drivers'] })
            setIsScoreModalOpen(false)
        } catch (error) {
            notify('error', 'Hata', 'Puan güncelleme başarısız.')
            throw error
        }
    }

    const handleDelete = async (driver: Driver) => {
        if (!driver.id) return
        const isPassive = !driver.aktif
        const confirmMsg = isPassive 
            ? `${driver.ad_soyad} adlı sürücüyü silmek istediğinize emin misiniz?`
            : `${driver.ad_soyad} adlı sürücüyü pasife çekmek istediğinize emin misiniz?`

        if (!window.confirm(confirmMsg)) return
        deleteMutation.mutate(driver)
    }

    const handleExport = async () => {
        try {
            const blob = await driverService.exportExcel({
                search: search || undefined,
                aktif_only: aktifOnly,
                ehliyet_sinifi: ehliyetFilter || undefined,
            })
            const url = window.URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `suruculer_export_${new Date().toISOString().split('T')[0]}.xlsx`
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
            const blob = await driverService.downloadTemplate()
            const url = window.URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = 'surucu_yukleme_sablonu.xlsx'
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
            await driverService.uploadExcel(file)
            notify("success", "Başarılı", "Sürücüler başarıyla içe aktarıldı.")
            queryClient.invalidateQueries({ queryKey: ['drivers'] })
        } catch (error) {
            notify("error", "Hata", "İçe aktarma başarısız.")
        }
    }

    return (
        <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-8"
        >
            <DriverHeader 
                onAdd={() => { setSelectedDriver(null); setIsModalOpen(true); }}
                onExport={handleExport}
                onDownloadTemplate={handleDownloadTemplate}
                onImport={handleImport}
            />

            <DriverFilters 
                search={search}
                setSearch={setSearch}
                viewMode={viewMode}
                setViewMode={setViewMode}
                aktifOnly={aktifOnly}
                setAktifOnly={setAktifOnly}
                ehliyetFilter={ehliyetFilter}
                setEhliyetFilter={setEhliyetFilter}
                ehliyetOptions={EHLIYET_OPTIONS}
            />

            {isLoading ? (
                <div className="flex items-center justify-center min-h-[400px]">
                    <div className="w-12 h-12 border-4 border-secondary border-t-transparent rounded-full animate-spin" />
                </div>
            ) : (
                <>
                    {viewMode === 'table' ? (
                        <div className="card glass overflow-hidden border-none shadow-premium">
                            <DriverTable 
                                drivers={drivers}
                                onEdit={(d) => { setSelectedDriver(d); setIsModalOpen(true); }}
                                onDelete={handleDelete}
                                onScoreClick={(d) => { setSelectedDriver(d); setIsScoreModalOpen(true); }}
                                onPerformanceClick={(d) => { setSelectedDriver(d); setIsPerformanceModalOpen(true); }}
                            />
                        </div>
                    ) : (
                        <DriverGrid 
                            drivers={drivers}
                            onEdit={(d) => { setSelectedDriver(d); setIsModalOpen(true); }}
                            onDelete={handleDelete}
                            onPerformanceClick={(d) => { setSelectedDriver(d); setIsPerformanceModalOpen(true); }}
                        />
                    )}
                </>
            )}

            <DriverModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onSave={handleSave}
                driver={selectedDriver}
            />

            <DriverScoreModal
                isOpen={isScoreModalOpen}
                onClose={() => setIsScoreModalOpen(false)}
                onSave={handleScoreSave}
                driver={selectedDriver}
            />

            <DriverPerformanceModal
                isOpen={isPerformanceModalOpen}
                onClose={() => setIsPerformanceModalOpen(false)}
                driver={selectedDriver}
            />
        </motion.div>
    )
}
