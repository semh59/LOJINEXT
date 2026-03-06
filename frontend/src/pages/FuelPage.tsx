import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { PremiumLayout } from '../components/layout/PremiumLayout'
import { FuelTable } from '../components/fuel/FuelTable'
import { FuelModal } from '../components/fuel/FuelModal'
import { FuelStats } from '../components/fuel/FuelStats'
import { FuelHeader } from '../components/fuel/FuelHeader'
import { FuelFilters } from '../components/fuel/FuelFilters'
import { ComparisonWidget } from '../components/fuel/ComparisonWidget'
import { FuelPagination } from '../components/fuel/FuelPagination'
import { fuelService } from '../services/api/fuel-service'
import { vehicleService } from '../services/api/vehicle-service'
import { predictionService } from '../services/api/prediction-service'
import { FuelRecord } from '../types'
import { useNotify } from '../context/NotificationContext'

export default function FuelPage() {
    const { notify } = useNotify()
    const queryClient = useQueryClient()

    // Modaller
    const [isModalOpen, setIsModalOpen] = useState(false)
    const [selectedRecord, setSelectedRecord] = useState<FuelRecord | null>(null)

    // Filter & Pagination State
    const [page, setPage] = useState(1)
    const [pageSize] = useState(20)
    const [startDate, setStartDate] = useState(
        new Date(new Date().setMonth(new Date().getMonth() - 1))
            .toISOString()
            .slice(0, 10),
    )
    const [endDate, setEndDate] = useState(new Date().toISOString().slice(0, 10))
    const [vehicleFilter, setVehicleFilter] = useState("")

    // React Query: Fetch Vehicles for selection
    const { data: vehiclesData = [] } = useQuery({
        queryKey: ['vehicles', 'minimal'],
        queryFn: () => vehicleService.getAll({ limit: 100 }),
    })
    const vehicles: any[] = Array.isArray(vehiclesData) ? vehiclesData : (vehiclesData as any)?.items || []

    // React Query: Fetch Prediction Comparison
    const { data: comparisonData, isLoading: isComparisonLoading } = useQuery({
        queryKey: ['predictionComparison'],
        queryFn: () => predictionService.getComparison(30),
    })

    // React Query: Fetch Fuel Records (Paginated)
    const { data: recordsResult, isLoading: isRecordsLoading } = useQuery({
        queryKey: ['fuelRecords', { startDate, endDate, vehicleFilter, page, pageSize }],
        queryFn: () => fuelService.getAll({
            baslangic_tarih: startDate,
            bitis_tarih: endDate,
            arac_id: vehicleFilter ? Number(vehicleFilter) : undefined,
            skip: (page - 1) * pageSize,
            limit: pageSize,
        }),
    })
    const records = recordsResult?.items || []
    const totalRecords = recordsResult?.total || 0

    // React Query: Fetch Fuel Stats
    const { data: stats = { 
        total_consumption: 0, total_cost: 0, avg_consumption: 0, total_distance: 0, avg_price: 0 
    } as any, isLoading: isStatsLoading } = useQuery({
        queryKey: ['fuelStats', { startDate, endDate, vehicleFilter }],
        queryFn: () => fuelService.getStats({
            baslangic_tarih: startDate,
            bitis_tarih: endDate,
            arac_id: vehicleFilter ? Number(vehicleFilter) : undefined,
        }),
    })

    // Mutations
    const handleSave = async (data: Partial<FuelRecord>) => {
        try {
            const payload = {
                ...data,
                fiyat_tl: data.birim_fiyat || (data as any).fiyat_tl,
            }
            
            if (selectedRecord?.id) {
                await fuelService.update(selectedRecord.id, payload)
                notify("success", "Güncellendi", "Kayıt başarıyla güncellendi.")
            } else {
                await fuelService.create(payload)
                notify("success", "Eklendi", "Yeni yakıt kaydı eklendi.")
                setPage(1) // Yeni kayıt eklendiğinde başa dön
            }
            
            // Otomatik tarih genişletme (Visibility fix)
            if (data.tarih) {
                if (data.tarih > endDate) setEndDate(data.tarih)
                if (data.tarih < startDate) setStartDate(data.tarih)
            }

            queryClient.invalidateQueries({ queryKey: ['fuelRecords'] })
            queryClient.invalidateQueries({ queryKey: ['fuelStats'] })
            setIsModalOpen(false)
        } catch (error: any) {
            notify("error", "Hata", "İşlem başarısız.")
        }
    }

    const handleDelete = async (record: FuelRecord) => {
        if (!window.confirm("Bu kaydı silmek istediğinize emin misiniz?")) return
        try {
            await fuelService.delete(record.id!)
            notify("success", "Başarılı", "Kayıt silindi")
            queryClient.invalidateQueries({ queryKey: ['fuelRecords'] })
            queryClient.invalidateQueries({ queryKey: ['fuelStats'] })
        } catch (error: any) {
            notify("error", "Hata", error.response?.data?.detail || "Silinemedi")
        }
    }

    const handleExport = async () => {
        try {
            const blob = await fuelService.exportExcel({ 
                baslangic_tarih: startDate, 
                bitis_tarih: endDate, 
                arac_id: vehicleFilter ? parseInt(vehicleFilter) : undefined 
            })
            const url = window.URL.createObjectURL(blob)
            const a = document.createElement("a")
            a.href = url
            a.download = `yakit_takip_${new Date().toISOString().split('T')[0]}.xlsx`
            document.body.appendChild(a)
            a.click()
            a.remove()
            window.URL.revokeObjectURL(url)
            notify("success", "Başarılı", "Yakıt verileri Excel olarak indirildi.")
        } catch (error) {
            notify("error", "Hata", "Dışa aktarma başarısız.")
        }
    }

    const handleDownloadTemplate = async () => {
        try {
            const blob = await fuelService.downloadTemplate()
            const url = window.URL.createObjectURL(blob)
            const a = document.createElement("a")
            a.href = url
            a.download = "yakit_import_sablonu.xlsx"
            document.body.appendChild(a)
            a.click()
            a.remove()
            window.URL.revokeObjectURL(url)
        } catch (error) {
            notify("error", "Hata", "Şablon indirilemedi.")
        }
    }

    const handleImport = async (file: File) => {
        try {
            await fuelService.uploadExcel(file)
            notify("success", "Başarılı", "Yakıt verileri içe aktarıldı.")
            queryClient.invalidateQueries({ queryKey: ['fuelRecords'] })
            queryClient.invalidateQueries({ queryKey: ['fuelStats'] })
        } catch (error) {
            notify("error", "Hata", "İçe aktarma başarısız.")
        }
    }

    return (
        <PremiumLayout title="Yakıt Kayıtları" primaryColor="#0df259">
            <div className="flex-1 w-full h-full p-6 animate-stagger-fade overflow-y-auto custom-scrollbar">
                <FuelHeader 
                    onAdd={() => { setSelectedRecord(null); setIsModalOpen(true); }}
                    onExport={handleExport}
                    onDownloadTemplate={handleDownloadTemplate}
                    onImport={handleImport}
                />

                <FuelStats stats={stats as any} loading={isStatsLoading} />

                {comparisonData && (
                    <ComparisonWidget data={comparisonData} isLoading={isComparisonLoading} />
                )}

                <FuelFilters 
                    startDate={startDate}
                    setStartDate={setStartDate}
                    endDate={endDate}
                    setEndDate={setEndDate}
                    vehicleFilter={vehicleFilter}
                    setVehicleFilter={setVehicleFilter}
                    vehicles={vehicles}
                    onFilter={() => {
                        setPage(1) // Filtre değişince başa dön
                        queryClient.invalidateQueries({ queryKey: ['fuelRecords'] })
                        queryClient.invalidateQueries({ queryKey: ['fuelStats'] })
                    }}
                />

                <div className="mt-6 border border-[#22492f] rounded-2xl bg-[#1a3825] overflow-hidden">
                    <FuelTable
                        records={records}
                        loading={isRecordsLoading}
                        onEdit={(r) => {
                            setSelectedRecord(r)
                            setIsModalOpen(true)
                        }}
                        onDelete={handleDelete}
                    />
                    
                    <FuelPagination
                        currentPage={page}
                        totalCount={totalRecords}
                        pageSize={pageSize}
                        onPageChange={setPage}
                    />
                </div>
            </div>

            <FuelModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                record={selectedRecord}
                onSave={handleSave}
            />
        </PremiumLayout>
    )
}
