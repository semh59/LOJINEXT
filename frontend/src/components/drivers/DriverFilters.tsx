import { Search, LayoutGrid, LayoutList } from 'lucide-react'
import { Input } from '../ui/Input'
import { cn } from '../../lib/utils'

interface DriverFiltersProps {
    search: string
    setSearch: (v: string) => void
    viewMode: 'table' | 'grid'
    setViewMode: (v: 'table' | 'grid') => void
    aktifOnly: boolean
    setAktifOnly: (v: boolean) => void
    ehliyetFilter: string
    setEhliyetFilter: (v: string) => void
    ehliyetOptions: string[]
}

export function DriverFilters({
    search, setSearch,
    viewMode, setViewMode,
    aktifOnly, setAktifOnly,
    ehliyetFilter, setEhliyetFilter,
    ehliyetOptions
}: DriverFiltersProps) {
    const handleReset = () => {
        setSearch('')
        setEhliyetFilter('')
        setAktifOnly(true)
    }

    return (
        <div className="bg-surface rounded-[12px] border border-border p-6 shadow-sm mb-8">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
                <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 flex-1">
                    <div className="relative flex-1 max-w-sm">
                        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-secondary group-focus-within:text-accent transition-colors" />
                        <Input
                            placeholder="İsim veya telefon ara..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            className="pl-10 h-10 bg-bg-elevated border-transparent text-primary placeholder:text-secondary focus:border-border focus:bg-surface transition-all rounded-[8px]"
                        />
                    </div>

                    <div className="flex items-center gap-1.5 bg-bg-elevated p-1 rounded-[10px] border border-border/50">
                        <button
                            onClick={() => setViewMode('table')}
                            className={cn(
                                "h-8 px-3 rounded-[6px] flex items-center gap-2 text-[11px] font-bold transition-all",
                                viewMode === 'table' ? "bg-surface text-accent shadow-sm border border-border/50" : "text-secondary hover:text-primary"
                            )}
                        >
                            <LayoutList className="w-3.5 h-3.5" /> Liste
                        </button>
                        <button
                            onClick={() => setViewMode('grid')}
                            className={cn(
                                "h-8 px-3 rounded-[6px] flex items-center gap-2 text-[11px] font-bold transition-all",
                                viewMode === 'grid' ? "bg-surface text-accent shadow-sm border border-border/50" : "text-secondary hover:text-primary"
                            )}
                        >
                            <LayoutGrid className="w-3.5 h-3.5" /> Kartlar
                        </button>
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    <button
                        onClick={() => setAktifOnly(!aktifOnly)}
                        className={cn(
                            "px-4 h-10 rounded-[8px] font-bold text-xs transition-all flex items-center gap-2 border",
                            aktifOnly
                                ? "bg-success/10 text-success border-success/20"
                                : "bg-bg-elevated text-secondary border-border hover:border-secondary"
                        )}
                    >
                        <div className={cn("w-1.5 h-1.5 rounded-full", aktifOnly ? "bg-success shadow-[0_0_8px_rgba(34,197,94,0.4)]" : "bg-border")} />
                        Sadece Aktif
                    </button>

                    <select
                        value={ehliyetFilter}
                        onChange={(e) => setEhliyetFilter(e.target.value)}
                        className="h-10 px-4 bg-bg-elevated border border-border rounded-[8px] text-xs font-bold outline-none text-primary focus:border-secondary transition-all"
                    >
                        <option value="">Tüm Ehliyetler</option>
                        {ehliyetOptions.filter(o => o).map(o => (
                             <option key={o} value={o}>{o} Sınıfı</option>
                         ))}
                     </select>

                    <button
                        onClick={handleReset}
                        className="h-10 px-4 text-xs font-bold text-secondary hover:text-primary transition-colors"
                    >
                        Sıfırla
                    </button>
                 </div>
            </div>
        </div>
    )
}
