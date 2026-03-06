import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Filter, LayoutGrid, List } from 'lucide-react'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import { cn } from '../../lib/utils'

interface TrailerFiltersProps {
    search: string
    setSearch: (v: string) => void
    showOnlyActive: boolean
    setShowOnlyActive: (v: boolean) => void
    isFilterOpen: boolean
    setIsFilterOpen: (v: boolean) => void
    filters: {
        marka: string
        model: string
        min_yil: string
        max_yil: string
    }
    setFilters: React.Dispatch<React.SetStateAction<{
        marka: string
        model: string
        min_yil: string
        max_yil: string
    }>>
    viewMode: 'grid' | 'list'
    setViewMode: (v: 'grid' | 'list') => void
}

export function TrailerFilters({
    search, setSearch,
    showOnlyActive, setShowOnlyActive,
    isFilterOpen, setIsFilterOpen,
    filters, setFilters,
    viewMode, setViewMode
}: TrailerFiltersProps) {
    const handleReset = () => {
        setFilters({ marka: '', model: '', min_yil: '', max_yil: '' })
        setSearch('')
    }

    const handleApplyFilters = () => setIsFilterOpen(false)

    return (
        <div className="bg-[#1a0121]/60 backdrop-blur-md p-4 rounded-xl border border-[#d006f9]/20 shadow-[0_0_15px_rgba(208,6,249,0.05)] w-full mb-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                
                {/* Search Bar */}
                <div className="relative flex-1 max-w-sm">
                    <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#d006f9]/60" />
                    <Input
                        placeholder="Dorse, plaka veya marka ara..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="pl-10 h-11 bg-black/40 border-[#d006f9]/30 text-white placeholder:text-white/30 focus:border-[#d006f9] focus:ring-[#d006f9]/20 rounded-xl"
                    />
                </div>

                {/* Filters & Toggles */}
                <div className="flex items-center gap-3">
                    <div className="flex bg-black/40 rounded-xl p-1 border border-white/10 mr-2">
                        <button
                            onClick={() => setViewMode('grid')}
                            className={cn(
                                "p-2 rounded-lg transition-all",
                                viewMode === 'grid' 
                                    ? "bg-[#d006f9]/20 text-[#d006f9] shadow-[0_0_10px_rgba(208,6,249,0.2)]" 
                                    : "text-white/40 hover:text-white hover:bg-white/5"
                            )}
                            title="Kart Görünümü"
                        >
                            <LayoutGrid className="w-4 h-4" />
                        </button>
                        <button
                            onClick={() => setViewMode('list')}
                            className={cn(
                                "p-2 rounded-lg transition-all",
                                viewMode === 'list' 
                                    ? "bg-[#d006f9]/20 text-[#d006f9] shadow-[0_0_10px_rgba(208,6,249,0.2)]" 
                                    : "text-white/40 hover:text-white hover:bg-white/5"
                            )}
                            title="Liste Görünümü"
                        >
                            <List className="w-4 h-4" />
                        </button>
                    </div>

                    <button
                        onClick={() => setShowOnlyActive(!showOnlyActive)}
                        className={cn(
                            "px-4 h-11 rounded-xl text-xs font-bold transition-all flex items-center gap-2 border",
                            showOnlyActive
                                ? "bg-[#0df259]/10 text-[#0df259] border-[#0df259]/20 shadow-[0_0_10px_rgba(13,242,89,0.1)]"
                                : "bg-black/20 text-white/50 border-white/10 hover:bg-black/40"
                        )}
                    >
                        <div className={cn("w-2 h-2 rounded-full", showOnlyActive ? "bg-[#0df259] shadow-[0_0_5px_#0df259] animate-pulse" : "bg-white/20")} />
                        Aktif Dorseler
                    </button>

                    <button
                        onClick={() => setIsFilterOpen(!isFilterOpen)}
                        className={cn(
                            "h-11 px-4 rounded-xl text-xs font-bold transition-all flex items-center gap-2 border",
                            isFilterOpen 
                                ? "bg-[#d006f9]/20 text-white border-[#d006f9]/50 shadow-[0_0_15px_rgba(208,6,249,0.2)]" 
                                : "bg-black/20 text-white/60 border-white/10 hover:bg-black/40 hover:text-white"
                        )}
                    >
                        <Filter className="w-4 h-4" /> Detaylı Filtre
                    </button>
                </div>
            </div>

            <AnimatePresence>
                {isFilterOpen && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-4 pt-4 border-t border-[#d006f9]/20"
                    >
                        <div className="space-y-1.5">
                            <label className="text-[10px] uppercase font-bold text-[#d006f9]/80 tracking-widest pl-1">Marka</label>
                            <Input
                                placeholder="Örn: Tırsan"
                                value={filters.marka}
                                onChange={(e) => setFilters(f => ({ ...f, marka: e.target.value }))}
                                className="h-10 bg-black/40 border-[#d006f9]/30 text-white placeholder:text-white/20 rounded-xl"
                            />
                        </div>
                        <div className="space-y-1.5">
                            <label className="text-[10px] uppercase font-bold text-[#d006f9]/80 tracking-widest pl-1">Tip</label>
                            <Input
                                placeholder="Örn: Frigo"
                                value={filters.model}
                                onChange={(e) => setFilters(f => ({ ...f, model: e.target.value }))}
                                className="h-10 bg-black/40 border-[#d006f9]/30 text-white placeholder:text-white/20 rounded-xl"
                            />
                        </div>
                        <div className="space-y-1.5">
                            <label className="text-[10px] uppercase font-bold text-[#d006f9]/80 tracking-widest pl-1">Minimum Yıl</label>
                            <Input
                                type="number"
                                placeholder="2015"
                                value={filters.min_yil}
                                onChange={(e) => setFilters(f => ({ ...f, min_yil: e.target.value }))}
                                className="h-10 bg-black/40 border-[#d006f9]/30 text-white placeholder:text-white/20 rounded-xl"
                            />
                        </div>
                        <div className="space-y-1.5">
                            <label className="text-[10px] uppercase font-bold text-[#d006f9]/80 tracking-widest pl-1">Maksimum Yıl</label>
                            <Input
                                type="number"
                                placeholder="2024"
                                value={filters.max_yil}
                                onChange={(e) => setFilters(f => ({ ...f, max_yil: e.target.value }))}
                                className="h-10 bg-black/40 border-[#d006f9]/30 text-white placeholder:text-white/20 rounded-xl"
                            />
                        </div>
                        <div className="col-span-full flex justify-end gap-2 mt-2">
                            <Button
                                variant="ghost"
                                onClick={handleReset}
                                className="text-white/60 hover:text-white"
                            >
                                Temizle
                            </Button>
                            <Button
                                variant="glossy-purple"
                                onClick={handleApplyFilters}
                            >
                                Uygula
                            </Button>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    )
}

