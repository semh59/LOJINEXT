import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react'
import { cn } from '../../lib/utils'

interface FuelPaginationProps {
    currentPage: number
    totalCount: number
    pageSize: number
    onPageChange: (page: number) => void
}

export function FuelPagination({ currentPage, totalCount, pageSize, onPageChange }: FuelPaginationProps) {
    const totalPages = Math.ceil(totalCount / pageSize)
    
    if (totalPages <= 1) return null

    const renderPageNumbers = () => {
        const pages = []
        const showEllipsis = totalPages > 7
        
        if (!showEllipsis) {
            for (let i = 1; i <= totalPages; i++) {
                pages.push(i)
            }
        } else {
            if (currentPage <= 4) {
                pages.push(1, 2, 3, 4, 5, '...', totalPages)
            } else if (currentPage >= totalPages - 3) {
                pages.push(1, '...', totalPages - 4, totalPages - 3, totalPages - 2, totalPages - 1, totalPages)
            } else {
                pages.push(1, '...', currentPage - 1, currentPage, currentPage + 1, '...', totalPages)
            }
        }

        return pages.map((p, i) => (
            <button
                key={i}
                disabled={p === '...'}
                onClick={() => typeof p === 'number' && onPageChange(p)}
                className={cn(
                    "w-10 h-10 rounded-xl text-sm font-black transition-all flex items-center justify-center",
                    p === currentPage 
                        ? "bg-[#0df259] text-[#050b0e] shadow-[0_0_15px_rgba(13,242,89,0.3)]" 
                        : p === '...' 
                            ? "text-slate-500 cursor-default" 
                            : "hover:bg-white/10 text-slate-300"
                )}
            >
                {p}
            </button>
        ))
    }

    return (
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 px-6 py-4 bg-black/40 border-t border-white/5 backdrop-blur-sm">
            <div className="text-xs font-bold text-slate-400 uppercase tracking-widest">
                Toplam <span className="text-[#0df259]">{totalCount.toLocaleString('tr-TR')}</span> Kayıt
            </div>
            
            <div className="flex items-center gap-1">
                <button
                    onClick={() => onPageChange(1)}
                    disabled={currentPage === 1}
                    className="hidden sm:flex p-2.5 rounded-xl hover:bg-white/10 text-slate-400 disabled:opacity-30 transition-all font-black items-center justify-center"
                    title="İlk Sayfa"
                >
                    <ChevronsLeft className="w-4.5 h-4.5" />
                </button>
                <button
                    onClick={() => onPageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                    className="px-3 py-2.5 rounded-xl hover:bg-white/10 text-slate-400 disabled:opacity-30 transition-all flex items-center gap-1 text-sm font-medium"
                >
                    <ChevronLeft className="w-4.5 h-4.5" />
                    Önceki
                </button>

                <div className="flex items-center gap-1 mx-2">
                    {renderPageNumbers()}
                </div>

                <button
                    onClick={() => onPageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                    className="px-3 py-2.5 rounded-xl hover:bg-white/10 text-slate-400 disabled:opacity-30 transition-all flex items-center gap-1 text-sm font-medium"
                >
                    Sonraki
                    <ChevronRight className="w-4.5 h-4.5" />
                </button>
                <button
                    onClick={() => onPageChange(totalPages)}
                    disabled={currentPage === totalPages}
                    className="hidden sm:flex p-2.5 rounded-xl hover:bg-white/10 text-slate-400 disabled:opacity-30 transition-all items-center justify-center"
                    title="Son Sayfa"
                >
                    <ChevronsRight className="w-4.5 h-4.5" />
                </button>
            </div>

            <div className="text-xs font-bold text-slate-400 uppercase tracking-widest sm:text-right">
                Sayfa <span className="text-white font-black">{currentPage}</span> / {totalPages}
            </div>
        </div>
    )
}
