import { useState, useEffect, useCallback, useRef } from 'react'
import { createPortal } from 'react-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { MainLayout } from '../components/layout/MainLayout'
import { DriverModal } from '../components/drivers/DriverModal'
import { DriverScoreModal } from '../components/drivers/DriverScoreModal'
import { DriverUploadModal } from '../components/drivers/DriverUploadModal'
import { driversApi } from '../services/api'
import { Driver } from '../types'
import {
    Plus, Search, Users, Download, Upload, RefreshCw,
    ChevronLeft, ChevronRight, MoreVertical, Edit2, Trash2,
    Star, Phone, Calendar, ShieldCheck, LayoutGrid, LayoutList
} from 'lucide-react'
import { Button } from '../components/ui/Button'
import { useNotify } from '../context/NotificationContext'
import { Input } from '../components/ui/Input'
import { cn } from '../lib/utils'

// Ehliyet sınıfları
const EHLIYET_OPTIONS = ['', 'B', 'C', 'CE', 'D', 'D1E', 'E', 'G']

// Score → Star mapping (Plan: 0.1-2.0 → 1-5 stars)
const scoreToStars = (score: number): number => {
    if (score >= 1.8) return 5
    if (score >= 1.5) return 4
    if (score >= 1.2) return 3
    if (score >= 0.8) return 2
    return 1
}

// Star renk kodları (Plana göre)
const getScoreColor = (score: number): string => {
    if (score >= 1.8) return '#10B981' // Mükemmel
    if (score >= 1.5) return '#3B82F6' // İyi
    if (score >= 1.2) return '#F59E0B' // Orta
    return '#EF4444' // Düşük
}

// Skeleton satırı
const SkeletonRow = () => (
    <tr className="animate-pulse">
        <td className="px-4 py-4"><div className="h-4 bg-neutral-200 rounded w-32" /></td>
        <td className="px-4 py-4"><div className="h-4 bg-neutral-200 rounded w-24" /></td>
        <td className="px-4 py-4"><div className="h-4 bg-neutral-200 rounded w-20" /></td>
        <td className="px-4 py-4"><div className="h-4 bg-neutral-200 rounded w-12" /></td>
        <td className="px-4 py-4"><div className="h-4 bg-neutral-200 rounded w-16" /></td>
        <td className="px-4 py-4"><div className="h-4 bg-neutral-200 rounded w-14" /></td>
        <td className="px-4 py-4"><div className="h-4 bg-neutral-200 rounded w-8" /></td>
    </tr>
)

export default function DriversPage() {
    const { notify } = useNotify()
    const [drivers, setDrivers] = useState<Driver[]>([])
    const [loading, setLoading] = useState(true)
    const [exporting, setExporting] = useState(false)

    // Modaller
    const [isModalOpen, setIsModalOpen] = useState(false)
    const [isScoreModalOpen, setIsScoreModalOpen] = useState(false)
    const [isUploadModalOpen, setIsUploadModalOpen] = useState(false)
    const [selectedDriver, setSelectedDriver] = useState<Driver | null>(null)

    // Görünüm modu
    const [viewMode, setViewMode] = useState<'table' | 'grid'>('table')

    // Filtreler
    const [search, setSearch] = useState('')
    const [filters, setFilters] = useState({
        aktif_only: true,
        ehliyet_sinifi: '',
    })

    // Pagination
    const [pagination, setPagination] = useState({
        page: 1,
        limit: 10,
        total: 0
    })

    // Actions dropdown
    const [openDropdown, setOpenDropdown] = useState<number | null>(null)
    const [dropdownPosition, setDropdownPosition] = useState<{ top: number; left: number } | null>(null)
    const buttonRefs = useRef<Map<number, HTMLButtonElement>>(new Map())

    const fetchDrivers = useCallback(async () => {
        setLoading(true)
        try {
            const data = await driversApi.getAll({
                skip: (pagination.page - 1) * pagination.limit,
                limit: pagination.limit,
                search: search || undefined,
                aktif_only: filters.aktif_only,
                ehliyet_sinifi: filters.ehliyet_sinifi || undefined,
            })
            setDrivers(data)
            // Backend düz array döner, total için length kullan
            setPagination(prev => ({ ...prev, total: data.length }))
        } catch (error) {
            console.error(error)
            notify('error', 'Hata', 'Sürücüler yüklenirken bir sorun oluştu.')
        } finally {
            setLoading(false)
        }
    }, [pagination.page, pagination.limit, search, filters, notify])

    // Debounced search
    useEffect(() => {
        const timer = setTimeout(fetchDrivers, 400)
        return () => clearTimeout(timer)
    }, [fetchDrivers])

    // Dropdown dışına tıklamada kapat
    useEffect(() => {
        const handleClickOutside = () => setOpenDropdown(null)
        document.addEventListener('click', handleClickOutside)
        return () => document.removeEventListener('click', handleClickOutside)
    }, [])

    const handleSave = async (data: Partial<Driver>) => {
        try {
            if (selectedDriver?.id) {
                await driversApi.update(selectedDriver.id, data)
                notify('success', 'Güncellendi', 'Sürücü bilgileri başarıyla güncellendi.')
            } else {
                await driversApi.create(data)
                notify('success', 'Eklendi', 'Yeni sürücü başarıyla eklendi.')
            }
            fetchDrivers()
            setIsModalOpen(false)
        } catch (error) {
            notify('error', 'Hata', 'İşlem sırasında bir hata oluştu.')
            throw error
        }
    }

    const handleScoreSave = async (score: number) => {
        if (!selectedDriver?.id) return
        try {
            await driversApi.updateScore(selectedDriver.id, score)
            notify('success', 'Puan Güncellendi', 'Sürücü puanı başarıyla güncellendi.')
            fetchDrivers()
            setIsScoreModalOpen(false)
        } catch (error) {
            notify('error', 'Hata', 'Puan güncelleme başarısız.')
            throw error
        }
    }

    const handleDelete = async (driver: Driver) => {
        if (!driver.id) return
        if (!window.confirm(`${driver.ad_soyad} adlı sürücüyü pasife çekmek istediğinize emin misiniz?`)) return

        // Optimistic update
        const prevDrivers = [...drivers]
        setDrivers(drivers.filter(d => d.id !== driver.id))

        try {
            await driversApi.delete(driver.id)
            notify('success', 'Silindi', 'Sürücü pasife çekildi.')
        } catch (error) {
            // Rollback
            setDrivers(prevDrivers)
            notify('error', 'Hata', 'Sürücü silinemedi.')
        }
    }

    const handleExport = async () => {
        setExporting(true)
        try {
            const blob = await driversApi.export({
                aktif_only: filters.aktif_only,
                search: search || undefined,
                ehliyet_sinifi: filters.ehliyet_sinifi || undefined,
            })
            const url = window.URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `suruculer_${new Date().toISOString().split('T')[0]}.xlsx`
            document.body.appendChild(a)
            a.click()
            window.URL.revokeObjectURL(url)
            document.body.removeChild(a)
            notify('success', 'İndirildi', 'Excel dosyası başarıyla indirildi.')
        } catch (error) {
            notify('error', 'Hata', 'Excel dosyası indirilemedi.')
        } finally {
            setExporting(false)
        }
    }

    const openModal = (driver?: Driver) => {
        setSelectedDriver(driver || null)
        setIsModalOpen(true)
    }

    const openScoreModal = (driver: Driver) => {
        setSelectedDriver(driver)
        setIsScoreModalOpen(true)
    }

    const totalPages = Math.ceil(drivers.length / pagination.limit) || 1

    // Performans göstergesi
    const renderStars = (score: number, manualScore?: number) => {
        const starCount = scoreToStars(score)
        const color = getScoreColor(score)

        return (
            <div className="flex flex-col gap-1">
                <div className="flex items-center gap-0.5">
                    {[1, 2, 3, 4, 5].map(i => (
                        <Star
                            key={i}
                            className={cn(
                                "w-3 h-3 transition-colors",
                                i <= starCount ? "fill-current" : "text-neutral-200"
                            )}
                            style={{ color: i <= starCount ? color : undefined }}
                        />
                    ))}
                </div>
                <div className="flex items-center gap-2 text-[10px] font-bold">
                    <span className="text-neutral-500">H:{score.toFixed(2)}</span>
                    {manualScore !== undefined && (
                        <span className="text-neutral-400">M:{manualScore.toFixed(1)}</span>
                    )}
                </div>
            </div>
        )
    }

    return (
        <MainLayout title="Sürücüler" breadcrumb="Filo Yönetimi / Sürücüler">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">

                {/* Header */}
                <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
                    <div>
                        <h1 className="text-3xl font-black text-brand-dark tracking-tighter flex items-center gap-3">
                            Sürücü Yönetimi
                            <span className="bg-primary/10 text-primary text-sm font-bold px-3 py-1 rounded-full">
                                {drivers.length} Kayıt
                            </span>
                        </h1>
                        <p className="text-neutral-500 font-medium mt-1">Şoför kadrosu ve performans takibi</p>
                    </div>

                    <div className="flex items-center gap-2 flex-wrap">
                        {/* View Toggle */}
                        <div className="flex items-center bg-neutral-100 rounded-xl p-1">
                            <button
                                onClick={() => setViewMode('table')}
                                className={cn(
                                    "p-2 rounded-lg transition-all",
                                    viewMode === 'table' ? "bg-white shadow-sm text-primary" : "text-neutral-400 hover:text-neutral-600"
                                )}
                            >
                                <LayoutList className="w-4 h-4" />
                            </button>
                            <button
                                onClick={() => setViewMode('grid')}
                                className={cn(
                                    "p-2 rounded-lg transition-all",
                                    viewMode === 'grid' ? "bg-white shadow-sm text-primary" : "text-neutral-400 hover:text-neutral-600"
                                )}
                            >
                                <LayoutGrid className="w-4 h-4" />
                            </button>
                        </div>

                        <Button variant="secondary" onClick={() => setIsUploadModalOpen(true)}>
                            <Upload className="w-4 h-4 mr-2" />
                            Excel Yükle
                        </Button>
                        <Button variant="secondary" onClick={handleExport} isLoading={exporting}>
                            <Download className="w-4 h-4 mr-2" />
                            Dışa Aktar
                        </Button>
                        <Button onClick={() => openModal()}>
                            <Plus className="w-4 h-4 mr-2" />
                            Yeni Sürücü
                        </Button>
                    </div>
                </div>

                {/* Filters Bar */}
                <div className="flex flex-col md:flex-row gap-4 items-start md:items-center bg-white/50 backdrop-blur-sm p-4 rounded-2xl border border-neutral-100">
                    {/* Search */}
                    <div className="relative flex-1 min-w-[200px]">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400" />
                        <Input
                            placeholder="İsim ile ara..."
                            className="pl-10 bg-white"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                        />
                    </div>

                    {/* Quick Filters */}
                    <div className="flex items-center gap-3 flex-wrap">
                        <label className="flex items-center gap-2 cursor-pointer px-3 py-2 bg-white rounded-xl border border-neutral-200 hover:border-primary/30 transition-colors">
                            <input
                                type="checkbox"
                                checked={filters.aktif_only}
                                onChange={(e) => setFilters(prev => ({ ...prev, aktif_only: e.target.checked }))}
                                className="w-4 h-4 text-primary rounded border-neutral-300 focus:ring-primary"
                            />
                            <span className="text-sm font-medium text-neutral-700">Sadece Aktif</span>
                        </label>

                        <select
                            value={filters.ehliyet_sinifi}
                            onChange={(e) => setFilters(prev => ({ ...prev, ehliyet_sinifi: e.target.value }))}
                            className="h-10 px-3 rounded-xl border border-neutral-200 bg-white text-sm font-medium focus:ring-2 focus:ring-primary/20 outline-none"
                        >
                            <option value="">Tüm Ehliyetler</option>
                            {EHLIYET_OPTIONS.filter(e => e).map(cls => (
                                <option key={cls} value={cls}>{cls} Sınıfı</option>
                            ))}
                        </select>

                        <button
                            onClick={fetchDrivers}
                            className="p-2 bg-white rounded-xl border border-neutral-200 text-neutral-400 hover:text-primary hover:border-primary/30 transition-colors"
                        >
                            <RefreshCw className="w-4 h-4" />
                        </button>
                    </div>
                </div>

                {/* Table View */}
                {viewMode === 'table' && (
                    <div className="bg-white rounded-2xl border border-neutral-100 shadow-sm overflow-visible">
                        <div className="overflow-x-auto overflow-y-visible">
                            <table className="w-full">
                                <thead>
                                    <tr className="bg-neutral-50/80 border-b border-neutral-100">
                                        <th className="px-4 py-3 text-left text-[11px] font-black text-neutral-500 uppercase tracking-wider" style={{ width: '180px' }}>Ad Soyad</th>
                                        <th className="px-4 py-3 text-left text-[11px] font-black text-neutral-500 uppercase tracking-wider" style={{ width: '130px' }}>Telefon</th>
                                        <th className="px-4 py-3 text-left text-[11px] font-black text-neutral-500 uppercase tracking-wider" style={{ width: '110px' }}>İşe Başlama</th>
                                        <th className="px-4 py-3 text-left text-[11px] font-black text-neutral-500 uppercase tracking-wider" style={{ width: '80px' }}>Ehliyet</th>
                                        <th className="px-4 py-3 text-left text-[11px] font-black text-neutral-500 uppercase tracking-wider" style={{ width: '120px' }}>Puan</th>
                                        <th className="px-4 py-3 text-left text-[11px] font-black text-neutral-500 uppercase tracking-wider" style={{ width: '90px' }}>Durum</th>
                                        <th className="px-4 py-3 text-center text-[11px] font-black text-neutral-500 uppercase tracking-wider" style={{ width: '80px' }}>İşlem</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-neutral-50">
                                    {loading ? (
                                        <>
                                            <SkeletonRow />
                                            <SkeletonRow />
                                            <SkeletonRow />
                                            <SkeletonRow />
                                        </>
                                    ) : drivers.length === 0 ? (
                                        <tr>
                                            <td colSpan={7} className="px-4 py-12 text-center">
                                                <div className="flex flex-col items-center">
                                                    <div className="w-16 h-16 bg-neutral-100 rounded-full flex items-center justify-center mb-4">
                                                        <Users className="w-8 h-8 text-neutral-400" />
                                                    </div>
                                                    <h3 className="text-lg font-bold text-neutral-900">Henüz Sürücü Eklenmemiş</h3>
                                                    <p className="text-neutral-500 mt-1">Sistemi kullanmaya başlamak için yeni bir sürücü ekleyin.</p>
                                                    <Button onClick={() => openModal()} className="mt-4">
                                                        <Plus className="w-4 h-4 mr-2" />
                                                        Yeni Sürücü Ekle
                                                    </Button>
                                                </div>
                                            </td>
                                        </tr>
                                    ) : (
                                        drivers.map((driver, index) => (
                                            <motion.tr
                                                key={driver.id}
                                                initial={{ opacity: 0, y: 10 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                transition={{ delay: index * 0.03 }}
                                                className="hover:bg-neutral-50/50 transition-colors group"
                                            >
                                                {/* Ad Soyad */}
                                                <td className="px-4 py-3">
                                                    <div className="flex items-center gap-3">
                                                        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary/20 to-brand/20 flex items-center justify-center text-primary font-bold text-sm">
                                                            {driver.ad_soyad?.[0]?.toUpperCase()}
                                                        </div>
                                                        <span className="font-bold text-neutral-900 truncate max-w-[120px]">
                                                            {driver.ad_soyad}
                                                        </span>
                                                    </div>
                                                </td>

                                                {/* Telefon (Maskelenmiş) */}
                                                <td className="px-4 py-3">
                                                    <div className="flex items-center gap-2 text-sm text-neutral-600">
                                                        <Phone className="w-3.5 h-3.5 text-neutral-400" />
                                                        <span className="font-medium">{driver.telefon_masked || driver.telefon || '-'}</span>
                                                    </div>
                                                </td>

                                                {/* İşe Başlama */}
                                                <td className="px-4 py-3 text-sm text-neutral-600">
                                                    <div className="flex items-center gap-2">
                                                        <Calendar className="w-3.5 h-3.5 text-neutral-400" />
                                                        {driver.ise_baslama ? new Date(driver.ise_baslama).toLocaleDateString('tr-TR') : '-'}
                                                    </div>
                                                </td>

                                                {/* Ehliyet */}
                                                <td className="px-4 py-3">
                                                    <span className="inline-flex items-center gap-1 px-2 py-1 bg-primary/5 text-primary text-xs font-bold rounded-lg border border-primary/10">
                                                        <ShieldCheck className="w-3 h-3" />
                                                        {driver.ehliyet_sinifi || 'B'}
                                                    </span>
                                                </td>

                                                {/* Puan */}
                                                <td className="px-4 py-3">
                                                    {renderStars(driver.score || 1.0, driver.manual_score)}
                                                </td>

                                                {/* Durum */}
                                                <td className="px-4 py-3">
                                                    <span className={cn(
                                                        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider",
                                                        driver.aktif
                                                            ? "bg-success/10 text-success-dark border border-success/20"
                                                            : "bg-danger/10 text-danger-dark border border-danger/20"
                                                    )}>
                                                        <span className={cn(
                                                            "w-1.5 h-1.5 rounded-full",
                                                            driver.aktif ? "bg-success animate-pulse" : "bg-danger"
                                                        )} />
                                                        {driver.aktif ? 'Aktif' : 'Pasif'}
                                                    </span>
                                                </td>

                                                {/* İşlemler Dropdown */}
                                                <td className="px-4 py-3 text-center">
                                                    <button
                                                        ref={(el) => {
                                                            if (el && driver.id) buttonRefs.current.set(driver.id, el)
                                                        }}
                                                        onClick={(e) => {
                                                            e.stopPropagation()
                                                            if (openDropdown === driver.id) {
                                                                setOpenDropdown(null)
                                                                setDropdownPosition(null)
                                                            } else {
                                                                const rect = e.currentTarget.getBoundingClientRect()
                                                                setDropdownPosition({
                                                                    top: rect.top - 10,
                                                                    left: rect.right - 192 // 192 = w-48 = 12rem
                                                                })
                                                                setOpenDropdown(driver.id!)
                                                            }
                                                        }}
                                                        className="p-2 rounded-lg hover:bg-neutral-100 text-neutral-400 hover:text-neutral-600 transition-colors"
                                                    >
                                                        <MoreVertical className="w-4 h-4" />
                                                    </button>


                                                    {openDropdown === driver.id && dropdownPosition && createPortal(
                                                        <AnimatePresence>
                                                            <motion.div
                                                                initial={{ opacity: 0, scale: 0.95 }}
                                                                animate={{ opacity: 1, scale: 1 }}
                                                                exit={{ opacity: 0, scale: 0.95 }}
                                                                style={{
                                                                    top: dropdownPosition.top,
                                                                    left: dropdownPosition.left
                                                                }}
                                                                className="fixed z-[9999] w-48 bg-white rounded-xl shadow-2xl border border-neutral-200 py-1 overflow-hidden"
                                                                onClick={(e) => e.stopPropagation()}
                                                            >
                                                                <button
                                                                    onClick={() => { openModal(driver); setOpenDropdown(null); }}
                                                                    className="w-full px-4 py-2.5 text-left text-sm font-medium text-neutral-700 hover:bg-neutral-50 flex items-center gap-3 transition-colors"
                                                                >
                                                                    <Edit2 className="w-4 h-4 text-neutral-400" />
                                                                    Düzenle
                                                                </button>
                                                                <button
                                                                    onClick={() => { openScoreModal(driver); setOpenDropdown(null); }}
                                                                    className="w-full px-4 py-2.5 text-left text-sm font-medium text-neutral-700 hover:bg-neutral-50 flex items-center gap-3 transition-colors"
                                                                >
                                                                    <Star className="w-4 h-4 text-amber-500" />
                                                                    Puan Ver
                                                                </button>
                                                                <div className="h-px bg-neutral-100 my-1" />
                                                                <button
                                                                    onClick={() => { handleDelete(driver); setOpenDropdown(null); }}
                                                                    className="w-full px-4 py-2.5 text-left text-sm font-medium text-danger hover:bg-danger/5 flex items-center gap-3 transition-colors"
                                                                >
                                                                    <Trash2 className="w-4 h-4" />
                                                                    Sil
                                                                </button>
                                                            </motion.div>
                                                        </AnimatePresence>,
                                                        document.body
                                                    )}
                                                </td>
                                            </motion.tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>

                        {/* Pagination */}
                        {!loading && drivers.length > 0 && (
                            <div className="flex items-center justify-between px-4 py-3 border-t border-neutral-100 bg-neutral-50/50">
                                <p className="text-sm text-neutral-500">
                                    Toplam <span className="font-bold text-neutral-700">{drivers.length}</span> kayıt
                                </p>
                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={() => setPagination(prev => ({ ...prev, page: Math.max(1, prev.page - 1) }))}
                                        disabled={pagination.page === 1}
                                        className="p-2 rounded-lg border border-neutral-200 text-neutral-400 hover:text-neutral-600 hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                    >
                                        <ChevronLeft className="w-4 h-4" />
                                    </button>
                                    <span className="px-4 py-2 text-sm font-medium text-neutral-700">
                                        Sayfa {pagination.page} / {totalPages}
                                    </span>
                                    <button
                                        onClick={() => setPagination(prev => ({ ...prev, page: Math.min(totalPages, prev.page + 1) }))}
                                        disabled={pagination.page === totalPages}
                                        className="p-2 rounded-lg border border-neutral-200 text-neutral-400 hover:text-neutral-600 hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                    >
                                        <ChevronRight className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Grid View (Mevcut Card Layout) */}
                {viewMode === 'grid' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                        {loading ? (
                            [1, 2, 3, 4].map(i => (
                                <div key={i} className="h-64 bg-white/50 rounded-2xl animate-pulse border border-neutral-100" />
                            ))
                        ) : drivers.length === 0 ? (
                            <div className="col-span-full flex flex-col items-center justify-center p-12 text-center border-2 border-dashed border-neutral-200 rounded-3xl bg-neutral-50/50">
                                <div className="w-16 h-16 bg-neutral-100 rounded-full flex items-center justify-center mb-4">
                                    <Users className="w-8 h-8 text-neutral-400" />
                                </div>
                                <h3 className="text-lg font-bold text-neutral-900">Henüz Sürücü Eklenmemiş</h3>
                                <p className="text-neutral-500 mt-1 max-w-sm">
                                    Sistemi kullanmaya başlamak için yeni bir sürücü ekleyin.
                                </p>
                                <Button onClick={() => openModal()} className="mt-4">
                                    <Plus className="w-4 h-4 mr-2" />
                                    Yeni Sürücü Ekle
                                </Button>
                            </div>
                        ) : (
                            drivers.map((driver, index) => (
                                <motion.div
                                    key={driver.id}
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: index * 0.05 }}
                                    className="group relative bg-white rounded-2xl p-6 border border-neutral-100 hover:shadow-xl hover:shadow-primary/5 transition-all duration-300"
                                >
                                    {/* Status Badge */}
                                    <div className="absolute top-4 right-4">
                                        <span className={cn(
                                            "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider",
                                            driver.aktif
                                                ? "bg-success/10 text-success-dark"
                                                : "bg-danger/10 text-danger-dark"
                                        )}>
                                            <span className={cn(
                                                "w-1.5 h-1.5 rounded-full",
                                                driver.aktif ? "bg-success animate-pulse" : "bg-danger"
                                            )} />
                                            {driver.aktif ? 'Aktif' : 'Pasif'}
                                        </span>
                                    </div>

                                    {/* Avatar & Name */}
                                    <div className="flex flex-col items-center text-center mb-4">
                                        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/20 to-brand/20 flex items-center justify-center text-primary text-2xl font-black mb-3">
                                            {driver.ad_soyad?.[0]?.toUpperCase()}
                                        </div>
                                        <h4 className="text-lg font-bold text-neutral-900 truncate w-full">{driver.ad_soyad}</h4>
                                        <span className="text-xs font-bold text-primary/70 mt-1">
                                            {driver.ehliyet_sinifi || 'B'} Sınıfı Ehliyet
                                        </span>
                                    </div>

                                    {/* Info */}
                                    <div className="space-y-2 mb-4 text-sm">
                                        <div className="flex items-center gap-2 text-neutral-600">
                                            <Phone className="w-4 h-4 text-neutral-400" />
                                            {driver.telefon_masked || driver.telefon || '-'}
                                        </div>
                                        <div className="flex items-center justify-center gap-4">
                                            {renderStars(driver.score || 1.0, driver.manual_score)}
                                        </div>
                                    </div>

                                    {/* Actions */}
                                    <div className="flex items-center gap-2 pt-4 border-t border-neutral-100">
                                        <button
                                            onClick={() => openScoreModal(driver)}
                                            className="flex-1 flex items-center justify-center gap-2 py-2 rounded-xl bg-amber-500 text-white text-xs font-bold hover:bg-amber-600 transition-colors"
                                        >
                                            <Star className="w-3.5 h-3.5 fill-white" /> Puanla
                                        </button>
                                        <button
                                            onClick={() => openModal(driver)}
                                            className="p-2 rounded-xl bg-neutral-100 text-neutral-400 hover:text-primary hover:bg-primary/10 transition-colors"
                                        >
                                            <Edit2 className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={() => handleDelete(driver)}
                                            className="p-2 rounded-xl bg-danger/10 text-danger hover:bg-danger hover:text-white transition-colors"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                </motion.div>
                            ))
                        )}
                    </div>
                )}

                {/* Modals */}
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

                <DriverUploadModal
                    isOpen={isUploadModalOpen}
                    onClose={() => setIsUploadModalOpen(false)}
                    onSuccess={fetchDrivers}
                />
            </motion.div>
        </MainLayout >
    )
}
