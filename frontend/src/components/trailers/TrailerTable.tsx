import { useState, useEffect } from 'react'
import { Dorse } from '../../types'
import { Edit2, Trash2, Container, Calendar, Weight, Disc, Activity } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '../../lib/utils'

interface TrailerTableProps {
    trailers: Dorse[]
    onEdit: (trailer: Dorse) => void
    onDelete: (trailer: Dorse) => void | Promise<void>
    onViewDetail: (trailer: Dorse) => void
    loading: boolean
    viewMode?: 'grid' | 'list'
}

export function TrailerTable({ trailers, loading, onEdit, onDelete, onViewDetail, viewMode = 'grid' }: TrailerTableProps) {
    const [deletingIds, setDeletingIds] = useState<Set<number>>(new Set())
    const [deletedIds, setDeletedIds] = useState<Set<number>>(new Set())

    useEffect(() => {
        setDeletedIds(new Set())
        setDeletingIds(new Set())
    }, [trailers])

    const handleOptimisticDelete = async (trailer: Dorse) => {
        if (!trailer.id) return
        
        const id = trailer.id
        setDeletedIds(prev => new Set([...prev, id]))
        setDeletingIds(prev => new Set([...prev, id]))

        try {
            await onDelete(trailer)
        } catch (error) {
            setDeletedIds(prev => {
                const next = new Set(prev)
                next.delete(id)
                return next
            })
        } finally {
            setDeletingIds(prev => {
                const next = new Set(prev)
                next.delete(id)
                return next
            })
        }
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center py-20">
                <div className="w-12 h-12 border-4 border-accent border-t-transparent rounded-full animate-spin" />
            </div>
        )
    }

    if (trailers.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center p-16 text-center border-2 border-dashed border-border rounded-[32px] bg-surface/40 backdrop-blur-md shadow-inner">
                <div className="w-20 h-20 bg-accent/10 rounded-2xl flex items-center justify-center mb-6 border border-accent/30 shadow-lg">
                    <Container className="w-10 h-10 text-accent" />
                </div>
                <h3 className="text-2xl font-black text-primary mb-2">Henüz Dorse Eklenmemiş</h3>
                <p className="text-secondary max-w-sm text-sm">
                    Filo yönetimine başlamak için sağ üstteki butondan yeni bir dorse ekleyerek operasyonlarınızı başlatın.
                </p>
            </div>
        )
    }

    return (
        <div className="w-full space-y-6">
            <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-black text-primary flex items-center gap-3">
                    <div className="w-10 h-10 bg-accent/20 border border-accent/40 rounded-xl flex items-center justify-center text-accent shadow-lg">
                        <Container className="w-5 h-5" />
                    </div>
                    Filo Dorseleri
                </h2>
                <div className="text-sm font-bold text-secondary bg-bg-elevated px-4 py-2 rounded-xl border border-border shadow-inner">
                    Toplam: <span className="text-accent ml-1">{trailers.filter(t => !deletedIds.has(t.id!)).length} Dorse</span>
                </div>
            </div>

            {viewMode === 'list' ? (
                <div className="bg-surface/80 backdrop-blur-xl border border-border rounded-[24px] shadow-lg overflow-hidden">
                    <div className="overflow-x-auto custom-scrollbar">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="border-b border-border bg-bg-elevated/40">
                                    <th className="p-5 text-xs font-black text-secondary uppercase tracking-widest">Plaka & Marka</th>
                                    <th className="p-5 text-xs font-black text-secondary uppercase tracking-widest">Tip & Yıl</th>
                                    <th className="p-5 text-xs font-black text-secondary uppercase tracking-widest">Teknik Parametreler</th>
                                    <th className="p-5 text-xs font-black text-secondary uppercase tracking-widest">Durum</th>
                                    <th className="p-5 text-xs font-black text-secondary uppercase tracking-widest text-right">İşlemler</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border">
                                <AnimatePresence>
                                    {trailers
                                        .filter(t => t.id && !deletedIds.has(t.id))
                                        .map((trailer, index) => (
                                            <motion.tr
                                                key={trailer.id}
                                                initial={{ opacity: 0, y: 10 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                exit={{ opacity: 0, scale: 0.95 }}
                                                transition={{ duration: 0.2, delay: index * 0.05 }}
                                                className={cn(
                                                    "group hover:bg-accent/5 transition-colors",
                                                    trailer.id && deletingIds.has(trailer.id) && "opacity-50 grayscale pointer-events-none bg-danger/10"
                                                )}
                                            >
                                                <td className="p-5">
                                                    <div className="flex items-center gap-4">
                                                        <div className="w-12 h-12 bg-bg-elevated border border-border rounded-2xl flex items-center justify-center shrink-0 shadow-inner">
                                                            <Container className="w-5 h-5 text-primary group-hover:text-accent transition-colors" />
                                                        </div>
                                                        <div>
                                                            <div className="font-black text-primary text-sm tracking-widest">{trailer.plaka}</div>
                                                            <div className="text-xs text-secondary uppercase tracking-wider">{trailer.marka || 'Bilinmiyor'}</div>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="p-5">
                                                    <div className="font-bold text-primary text-sm">{trailer.tipi}</div>
                                                    <div className="text-xs text-secondary">{trailer.yil || '-'} Model</div>
                                                </td>
                                                <td className="p-5">
                                                    <div className="flex gap-4 text-sm">
                                                        <div className="flex items-center gap-1.5 text-primary">
                                                            <Weight className="w-3.5 h-3.5 text-secondary" />
                                                            <span className="font-bold">{trailer.bos_agirlik_kg?.toLocaleString('tr-TR') || '-'} kg</span>
                                                        </div>
                                                        <div className="flex items-center gap-1.5 text-primary">
                                                            <Disc className="w-3.5 h-3.5 text-secondary" />
                                                            <span className="font-bold">{trailer.lastik_sayisi || '-'} Lastik</span>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="p-5">
                                                    <span className={cn(
                                                        "text-[10px] font-bold px-3 py-1.5 rounded-full border inline-flex items-center gap-1.5 uppercase tracking-widest",
                                                        trailer.aktif
                                                            ? "bg-success/10 text-success border-success/30"
                                                            : "bg-bg-elevated text-secondary border-border"
                                                    )}>
                                                        <span className={cn(
                                                            "w-2 h-2 rounded-full",
                                                            trailer.aktif ? "bg-success animate-pulse" : "bg-secondary"
                                                        )}></span>
                                                        {trailer.aktif ? 'AKTİF' : 'PASİF'}
                                                    </span>
                                                </td>
                                                <td className="p-5 text-right">
                                                    <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                        <button
                                                            onClick={(e) => { e.stopPropagation(); onViewDetail(trailer); }}
                                                            className="h-9 px-3 rounded-xl bg-accent/10 text-accent border border-accent/20 hover:bg-accent/20 font-bold text-xs flex items-center gap-2 transition-all"
                                                        >
                                                            <Activity className="w-3.5 h-3.5" /> Detay
                                                        </button>
                                                        <button
                                                            onClick={(e) => { e.stopPropagation(); onEdit(trailer); }}
                                                            className="w-9 h-9 rounded-xl bg-bg-elevated border border-border text-secondary hover:text-primary hover:bg-surface flex items-center justify-center transition-all"
                                                        >
                                                            <Edit2 className="w-4 h-4" />
                                                        </button>
                                                        <button
                                                            onClick={(e) => { e.stopPropagation(); trailer.id && handleOptimisticDelete(trailer); }}
                                                            disabled={!!trailer.id && deletingIds.has(trailer.id)}
                                                            className="w-9 h-9 rounded-xl bg-danger/10 border border-danger/20 text-danger hover:bg-danger/20 flex items-center justify-center transition-all disabled:opacity-50"
                                                        >
                                                            <Trash2 className="w-4 h-4" />
                                                        </button>
                                                    </div>
                                                </td>
                                            </motion.tr>
                                        ))}
                                </AnimatePresence>
                            </tbody>
                        </table>
                    </div>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    <AnimatePresence>
                        {trailers
                            .filter(t => t.id && !deletedIds.has(t.id))
                            .map((trailer, index) => (
                                <motion.div
                                    key={trailer.id}
                                    initial={{ opacity: 0, scale: 0.95, y: 20 }}
                                    animate={{ opacity: 1, scale: 1, y: 0 }}
                                    exit={{ opacity: 0, scale: 0.9, y: -20 }}
                                    transition={{ duration: 0.3, delay: index * 0.05 }}
                                    className={cn(
                                        "bg-surface/80 backdrop-blur-xl border border-border rounded-[24px] p-6 shadow-lg transition-all hover:-translate-y-1 hover:shadow-accent/5 hover:border-accent/40 flex flex-col relative overflow-hidden group",
                                        trailer.id && deletingIds.has(trailer.id) && "opacity-50 grayscale pointer-events-none"
                                    )}
                                >
                                    {/* Background glow effect on hover */}
                                    <div className="absolute top-0 right-0 w-32 h-32 bg-accent/5 rounded-full blur-[40px] -translate-y-1/2 translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                                    
                                    {/* Status Indicator (Top Right) */}
                                    <div className="absolute top-6 right-6 z-10">
                                        <span className={cn(
                                            "text-[10px] font-bold px-3 py-1.5 rounded-full border flex items-center gap-1.5 uppercase tracking-widest shadow-sm",
                                            trailer.aktif
                                                ? "bg-success/10 text-success border-success/30 shadow-success/10"
                                                : "bg-bg-elevated text-secondary border-border"
                                        )}>
                                            <span className={cn(
                                                "w-2 h-2 rounded-full",
                                                trailer.aktif ? "bg-success shadow-sm animate-pulse" : "bg-secondary"
                                            )}></span>
                                            {trailer.aktif ? 'AKTİF' : 'PASİF'}
                                        </span>
                                    </div>

                                    {/* Trailer Header */}
                                    <div className="flex items-start gap-4 mb-6 relative z-10">
                                        <div className="w-14 h-14 bg-bg-elevated border border-border rounded-2xl flex items-center justify-center shrink-0 shadow-inner">
                                            <Container className="w-7 h-7 text-primary group-hover:text-accent transition-colors" />
                                        </div>
                                        <div className="flex-1 min-w-0 pr-20">
                                            <div className="bg-bg-elevated text-accent text-xs font-black tracking-widest px-2.5 py-1 rounded inline-flex items-center border border-border mb-2 shadow-md">
                                                {trailer.plaka}
                                            </div>
                                            <h3 className="text-lg font-black text-primary truncate group-hover:text-accent transition-colors">
                                                {trailer.marka || 'Bilinmiyor'}
                                            </h3>
                                            <p className="text-[10px] text-secondary font-bold uppercase tracking-wider">{trailer.tipi}</p>
                                        </div>
                                    </div>

                                    {/* Stats Grid */}
                                    <div className="grid grid-cols-2 gap-3 mb-6 relative z-10">
                                        <div className="bg-bg-elevated border border-border rounded-xl p-3 flex flex-col gap-1">
                                            <div className="flex items-center gap-1.5 text-secondary mb-0.5">
                                                <Calendar className="w-3.5 h-3.5" />
                                                <span className="text-[10px] font-bold uppercase tracking-wider">Model Yılı</span>
                                            </div>
                                            <span className="text-sm font-bold text-primary">{trailer.yil || '-'}</span>
                                        </div>
                                        <div className="bg-bg-elevated border border-border rounded-xl p-3 flex flex-col gap-1">
                                            <div className="flex items-center gap-1.5 text-secondary mb-0.5">
                                                <Weight className="w-3.5 h-3.5" />
                                                <span className="text-[10px] font-bold uppercase tracking-wider">Boş Ağırlık</span>
                                            </div>
                                            <span className="text-sm font-bold text-primary">{trailer.bos_agirlik_kg?.toLocaleString('tr-TR') || '-'} kg</span>
                                        </div>
                                        <div className="col-span-2 bg-bg-elevated border border-border rounded-xl p-3 flex flex-col gap-1">
                                            <div className="flex items-center gap-1.5 text-secondary mb-0.5">
                                                <Disc className="w-3.5 h-3.5" />
                                                <span className="text-[10px] font-bold uppercase tracking-wider">Lastik Sayısı</span>
                                            </div>
                                            <span className="text-sm font-bold text-primary">{trailer.lastik_sayisi || '-'} Adet</span>
                                        </div>
                                    </div>

                                    <div className="flex-1" />

                                    {/* Actions Footer */}
                                    <div className="flex justify-between items-center pt-4 border-t border-border relative z-10">
                                        <button
                                            onClick={() => onViewDetail(trailer)}
                                            className="h-10 px-4 rounded-xl bg-accent/10 text-accent border border-accent/20 hover:bg-accent/20 hover:border-accent/40 font-bold text-xs flex items-center gap-2 transition-all"
                                        >
                                            <Activity className="w-4 h-4" />
                                            Detaylar
                                        </button>
                                        
                                        <div className="flex items-center gap-2">
                                            <button
                                                onClick={() => onEdit(trailer)}
                                                className="w-10 h-10 rounded-xl bg-bg-elevated border border-border text-secondary hover:text-primary hover:bg-surface flex items-center justify-center transition-all"
                                                title="Düzenle"
                                            >
                                                <Edit2 className="w-4 h-4" />
                                            </button>
                                            <button
                                                onClick={() => trailer.id && handleOptimisticDelete(trailer)}
                                                disabled={!!trailer.id && deletingIds.has(trailer.id)}
                                                className="w-10 h-10 rounded-xl bg-danger/10 border border-danger/20 text-danger hover:bg-danger/20 flex items-center justify-center transition-all disabled:opacity-50"
                                                title="Sil"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </div>
                                </motion.div>
                            ))}
                    </AnimatePresence>
                </div>
            )}
        </div>
    )
}
