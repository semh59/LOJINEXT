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
                    "w-9 h-9 rounded-lg text-xs font-bold transition-all flex items-center justify-center",
                    p === currentPage 
                        ? "bg-accent text-bg-base shadow-sm" 
                        : p === '...' 
                            ? "text-secondary cursor-default" 
                            : "hover:bg-bg-elevated text-secondary border border-transparent hover:border-border"
                )}
            >
                {p}
            </button>
        ))
    }

    return (
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 px-6 py-4 bg-bg-elevated/30 border-t border-border backdrop-blur-sm">
            <div className="text-[10px] font-bold text-secondary uppercase tracking-widest">
                TOPLAM <span className="text-accent">{totalCount.toLocaleString('tr-TR')}</span> KAYIT
            </div>
            
            <div className="flex items-center gap-1">
                <button
                    onClick={() => onPageChange(1)}
                    disabled={currentPage === 1}
                    className="hidden sm:flex p-2.5 rounded-xl hover:bg-surface text-secondary disabled:opacity-30 transition-all font-black items-center justify-center"
                    title="İlk Sayfa"
                >
                    <ChevronsLeft className="w-4.5 h-4.5" />
                </button>
                <button
                    onClick={() => onPageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                    className="px-3 py-2.5 rounded-xl hover:bg-surface text-secondary disabled:opacity-30 transition-all flex items-center gap-1 text-sm font-medium"
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
                    className="px-3 py-2.5 rounded-xl hover:bg-surface text-secondary disabled:opacity-30 transition-all flex items-center gap-1 text-sm font-medium"
                >
                    Sonraki
                    <ChevronRight className="w-4.5 h-4.5" />
                </button>
                <button
                    onClick={() => onPageChange(totalPages)}
                    disabled={currentPage === totalPages}
                    className="hidden sm:flex p-2.5 rounded-xl hover:bg-surface text-secondary disabled:opacity-30 transition-all items-center justify-center"
                    title="Son Sayfa"
                >
                    <ChevronsRight className="w-4.5 h-4.5" />
                </button>
            </div>

            <div className="text-xs font-bold text-secondary uppercase tracking-widest sm:text-right">
                Sayfa <span className="text-primary font-black">{currentPage}</span> / {totalPages}
            </div>
        </div>
    )
}
