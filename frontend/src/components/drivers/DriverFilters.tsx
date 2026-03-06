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
    return (
        <div className="glass-card p-6 border border-white/5 shadow-[0_0_50px_rgba(208,6,249,0.03)] mb-8">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
                <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 flex-1">
                    <div className="relative flex-1 max-w-md">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 group-focus-within:text-[#d006f9] transition-colors" />
                        <Input
                            placeholder="İsim veya telefon ara..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            className="pl-11 h-12 bg-black/20 border-white/5 text-white placeholder:text-slate-600 focus:border-[#d006f9]/40 focus:bg-black/40 transition-all rounded-xl shadow-inner outline-none"
                        />
                    </div>

                    <div className="flex items-center gap-2 bg-black/20 p-1.5 rounded-2xl border border-white/5 backdrop-blur-sm shadow-inner">
                        <button
                            onClick={() => setViewMode('table')}
                            className={cn(
                                "h-9 px-4 rounded-xl flex items-center gap-2 text-xs font-bold transition-all",
                                viewMode === 'table' ? "bg-[#d006f9]/10 text-[#d006f9] border border-[#d006f9]/30 shadow-[0_0_15px_rgba(208,6,249,0.2)]" : "text-slate-500 hover:text-slate-300"
                            )}
                        >
                            <LayoutList className="w-4 h-4" /> Liste
                        </button>
                        <button
                            onClick={() => setViewMode('grid')}
                            className={cn(
                                "h-9 px-4 rounded-xl flex items-center gap-2 text-xs font-bold transition-all",
                                viewMode === 'grid' ? "bg-[#d006f9]/10 text-[#d006f9] border border-[#d006f9]/30 shadow-[0_0_15px_rgba(208,6,249,0.2)]" : "text-slate-500 hover:text-slate-300"
                            )}
                        >
                            <LayoutGrid className="w-4 h-4" /> Kartlar
                        </button>
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    <button
                        onClick={() => setAktifOnly(!aktifOnly)}
                        className={cn(
                            "px-4 h-12 rounded-xl font-semibold text-sm transition-all flex items-center gap-2 border shadow-lg",
                            aktifOnly
                                ? "bg-[#0df259]/10 text-[#0df259] border-[#0df259]/30 shadow-[0_0_15px_rgba(13,242,89,0.15)]"
                                : "bg-black/40 text-white/50 border-[#d006f9]/20 hover:border-[#d006f9]/40"
                        )}
                    >
                        <div className={cn("w-2 h-2 rounded-full", aktifOnly ? "bg-[#0df259] shadow-[0_0_8px_#0df259] animate-pulse" : "bg-white/20")} />
                        Sadece Aktif
                    </button>

                    <select
                        value={ehliyetFilter}
                        onChange={(e) => setEhliyetFilter(e.target.value)}
                        className="h-12 px-4 bg-black/20 border border-white/5 rounded-xl text-sm font-bold outline-none text-slate-100 focus:border-[#d006f9]/40 transition-all shadow-inner"
                    >
                        <option value="" className="bg-[#050b0e]">Tüm Ehliyetler</option>
                        {ehliyetOptions.filter(o => o).map(o => (
                            <option key={o} value={o} className="bg-[#050b0e]">{o} Sınıfı</option>
                        ))}
                    </select>
                </div>
            </div>
        </div>
    )
}
