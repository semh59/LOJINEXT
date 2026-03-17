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
    setFilters: (val: any) => void
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
        <div className="bg-surface/60 backdrop-blur-md p-4 rounded-xl border border-border shadow-sm w-full mb-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                
                {/* Search Bar */}
                <div className="relative flex-1 max-w-sm">
                    <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-accent/60" />
                    <Input
                        placeholder="Dorse, plaka veya marka ara..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="pl-10 h-11 bg-bg-elevated border-border text-primary placeholder:text-secondary focus:border-accent focus:ring-accent/20 rounded-xl"
                    />
                </div>

                {/* Filters & Toggles */}
                <div className="flex items-center gap-3">
                    <div className="flex bg-bg-elevated rounded-xl p-1 border border-border mr-2">
                        <button
                            onClick={() => setViewMode('grid')}
                            className={cn(
                                "p-2 rounded-lg transition-all",
                                viewMode === 'grid' 
                                    ? "bg-accent/20 text-accent shadow-lg shadow-accent/5" 
                                    : "text-secondary hover:text-primary hover:bg-bg-elevated"
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
                                    ? "bg-accent/20 text-accent shadow-lg shadow-accent/5" 
                                    : "text-secondary hover:text-primary hover:bg-bg-elevated"
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
                                ? "bg-success/10 text-success border-success/20 shadow-lg shadow-success/5"
                                : "bg-bg-elevated text-secondary border-border hover:bg-surface"
                        )}
                    >
                        <div className={cn("w-2 h-2 rounded-full", showOnlyActive ? "bg-success shadow-[0_0_5px_var(--success)] animate-pulse" : "bg-border/40")} />
                        Aktif Dorseler
                    </button>

                    <button
                        onClick={() => setIsFilterOpen(!isFilterOpen)}
                        className={cn(
                            "h-11 px-4 rounded-xl text-xs font-bold transition-all flex items-center gap-2 border",
                            isFilterOpen 
                                ? "bg-accent/20 text-primary border-accent/50 shadow-lg shadow-accent/5" 
                                : "bg-bg-elevated text-secondary border-border hover:bg-surface hover:text-primary"
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
                        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-4 pt-4 border-t border-border"
                    >
                        <div className="space-y-1.5">
                            <label className="text-[10px] uppercase font-bold text-accent/80 tracking-widest pl-1">Marka</label>
                            <Input
                                placeholder="Örn: Tırsan"
                                value={filters.marka}
                                onChange={(e) => setFilters((f: any) => ({ ...f, marka: e.target.value }))}
                                className="h-10 bg-bg-elevated/40 border-accent/30 text-primary placeholder:text-secondary rounded-xl"
                            />
                        </div>
                        <div className="space-y-1.5">
                            <label className="text-[10px] uppercase font-bold text-accent/80 tracking-widest pl-1">Tip</label>
                            <Input
                                placeholder="Örn: Frigo"
                                value={filters.model}
                                onChange={(e) => setFilters((f: any) => ({ ...f, model: e.target.value }))}
                                className="h-10 bg-bg-elevated border-border text-primary placeholder:text-secondary rounded-xl"
                            />
                        </div>
                        <div className="space-y-1.5">
                            <label className="text-[10px] uppercase font-bold text-accent/80 tracking-widest pl-1">Minimum Yıl</label>
                            <Input
                                type="number"
                                placeholder="2015"
                                value={filters.min_yil}
                                onChange={(e) => setFilters((f: any) => ({ ...f, min_yil: e.target.value }))}
                                className="h-10 bg-bg-elevated/40 border-accent/30 text-primary placeholder:text-secondary rounded-xl"
                            />
                        </div>
                        <div className="space-y-1.5">
                            <label className="text-[10px] uppercase font-bold text-accent/80 tracking-widest pl-1">Maksimum Yıl</label>
                            <Input
                                type="number"
                                placeholder="2024"
                                value={filters.max_yil}
                                onChange={(e) => setFilters((f: any) => ({ ...f, max_yil: e.target.value }))}
                                className="h-10 bg-bg-elevated/40 border-accent/30 text-primary placeholder:text-secondary rounded-xl"
                            />
                        </div>
                        <div className="col-span-full flex justify-end gap-2 mt-2">
                            <Button
                                variant="ghost"
                                onClick={handleReset}
                                className="text-secondary hover:text-primary"
                            >
                                Temizle
                            </Button>
                            <Button
                                variant="primary"
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

