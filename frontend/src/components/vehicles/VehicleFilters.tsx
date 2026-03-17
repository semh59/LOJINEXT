import { motion, AnimatePresence } from 'framer-motion'
import { Search, Filter } from 'lucide-react'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import { cn } from '../../lib/utils'

interface VehicleFiltersProps {
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
}

export function VehicleFilters({
    search, setSearch,
    showOnlyActive, setShowOnlyActive,
    isFilterOpen, setIsFilterOpen,
    filters, setFilters
}: VehicleFiltersProps) {
    const handleReset = () => {
        setFilters({ marka: '', model: '', min_yil: '', max_yil: '' })
        setSearch('')
    }

    const handleApplyFilters = () => setIsFilterOpen(false)

    return (
        <div className="bg-surface p-4 rounded-[10px] border border-border shadow-sm w-full mb-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                
                {/* Search Bar */}
                <div className="relative flex-1 max-w-sm">
                    <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-secondary" />
                    <Input
                        placeholder="Araç, plaka veya marka ara..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="pl-10"
                    />
                </div>

                {/* Filters & Toggles */}
                <div className="flex items-center gap-3">
                    <button
                        onClick={() => setShowOnlyActive(!showOnlyActive)}
                        className={cn(
                            "px-4 h-[40px] rounded-[6px] text-xs font-bold transition-all flex items-center gap-2 border",
                            showOnlyActive
                                ? "bg-success/10 text-success border-success/20"
                                : "bg-surface text-secondary border-border hover:bg-bg-elevated"
                        )}
                    >
                        <div className={cn("w-2 h-2 rounded-full", showOnlyActive ? "bg-success shadow-[0_0_8px_rgba(34,197,94,0.3)]" : "bg-border")} />
                        Aktif Araçlar
                    </button>

                    <button
                        onClick={() => setIsFilterOpen(!isFilterOpen)}
                        className={cn(
                            "h-[40px] px-4 rounded-[6px] text-xs font-bold transition-all flex items-center gap-2 border",
                            isFilterOpen 
                                ? "bg-accent/10 text-accent border-accent/20" 
                                : "bg-surface text-secondary border-border hover:bg-bg-elevated hover:text-primary"
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
                            <label className="text-[10px] uppercase font-bold text-secondary tracking-widest pl-1">Marka</label>
                            <Input
                                placeholder="Örn: Mercedes"
                                value={filters.marka}
                                onChange={(e) => setFilters((f: any) => ({ ...f, marka: e.target.value }))}
                                className="h-10 bg-bg-elevated border-border text-primary placeholder:text-secondary rounded-xl"
                            />
                        </div>
                        <div className="space-y-1.5">
                            <label className="text-[10px] uppercase font-bold text-secondary tracking-widest pl-1">Model</label>
                            <Input
                                placeholder="Örn: Actros"
                                value={filters.model}
                                onChange={(e) => setFilters((f: any) => ({ ...f, model: e.target.value }))}
                                className="h-10 bg-bg-elevated border-border text-primary placeholder:text-secondary rounded-xl"
                            />
                        </div>
                        <div className="space-y-1.5">
                            <label className="text-[10px] uppercase font-bold text-secondary tracking-widest pl-1">Minimum Yıl</label>
                            <Input
                                type="number"
                                placeholder="2015"
                                value={filters.min_yil}
                                onChange={(e) => setFilters((f: any) => ({ ...f, min_yil: e.target.value }))}
                                className="h-10 bg-bg-elevated border-border text-primary placeholder:text-secondary rounded-xl"
                            />
                        </div>
                        <div className="space-y-1.5">
                            <label className="text-[10px] uppercase font-bold text-secondary tracking-widest pl-1">Maksimum Yıl</label>
                            <Input
                                type="number"
                                placeholder="2024"
                                value={filters.max_yil}
                                onChange={(e) => setFilters((f: any) => ({ ...f, max_yil: e.target.value }))}
                                className="h-10 bg-bg-elevated border-border text-primary placeholder:text-secondary rounded-xl"
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
