import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { dorseService } from '../../services/dorseService'
import { TrailerHeader } from '../trailers/TrailerHeader'
import { TrailerTable } from '../trailers/TrailerTable'
import { TrailerFilters } from '../trailers/TrailerFilters'
import { TrailerModal } from '../trailers/TrailerModal'
import TrailerDetailModal from '../trailers/TrailerDetailModal'
import TrailerDeleteModal from '../trailers/TrailerDeleteModal'
import { Dorse } from '../../types'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { toast } from 'sonner'
import { cn } from '../../lib/utils'


const ITEMS_PER_PAGE = 8

export function TrailersModule() {
    const queryClient = useQueryClient()
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
    const [search, setSearch] = useState('')
    const [showOnlyActive, setShowOnlyActive] = useState(true)
    const [isFilterOpen, setIsFilterOpen] = useState(false)
    const [currentPage, setCurrentPage] = useState(1)
    const [filters, setFilters] = useState({
        marka: '',
        model: '',
        min_yil: '',
        max_yil: ''
    })

    const [isModalOpen, setIsModalOpen] = useState(false)
    const [isDetailOpen, setIsDetailOpen] = useState(false)
    const [isDeleteOpen, setIsDeleteOpen] = useState(false)
    const [selectedTrailer, setSelectedTrailer] = useState<Dorse | null>(null)

    const { data: trailers = [], isLoading } = useQuery({
        queryKey: ['trailers', search, showOnlyActive, filters],
        queryFn: () => dorseService.getAll({ 
            search, 
            aktif_only: showOnlyActive,
            marka: filters.marka,
            model: filters.model,
            min_yil: filters.min_yil ? parseInt(filters.min_yil) : undefined,
            max_yil: filters.max_yil ? parseInt(filters.max_yil) : undefined
        }),
    })

    const deleteMutation = useMutation({
        mutationFn: (id: number) => dorseService.delete(id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['trailers'] })
            setIsDeleteOpen(false)
            setSelectedTrailer(null)
            toast.success('Dorse başarıyla silindi')
        }
    })

    const handleEdit = (trailer: Dorse) => {
        setSelectedTrailer(trailer)
        setIsModalOpen(true)
    }

    const handleDelete = (trailer: Dorse) => {
        setSelectedTrailer(trailer)
        setIsDeleteOpen(true)
    }

    const handleViewDetail = (trailer: Dorse) => {
        setSelectedTrailer(trailer)
        setIsDetailOpen(true)
    }

    const handleImport = async (file: File) => {
        try {
            await dorseService.uploadExcel(file)
            queryClient.invalidateQueries({ queryKey: ['trailers'] })
            toast.success('Dorseler başarıyla içe aktarıldı')
        } catch (error) {
            console.error('Import error:', error)
            toast.error('İçe aktarma sırasında bir hata oluştu')
        }
    }

    // Pagination logic
    const totalPages = Math.ceil(trailers.length / ITEMS_PER_PAGE)
    const paginatedTrailers = trailers.slice(
        (currentPage - 1) * ITEMS_PER_PAGE,
        currentPage * ITEMS_PER_PAGE
    )

    return (
        <div className="space-y-6">
            <TrailerHeader 
                onAdd={() => {
                    setSelectedTrailer(null)
                    setIsModalOpen(true)
                }}
                onImport={handleImport}
                onExport={() => dorseService.exportExcel()}
                onDownloadTemplate={() => dorseService.downloadTemplate()}
            />

            <div className="bg-[#1a0121]/40 backdrop-blur-md rounded-[32px] border border-[#d006f9]/10 p-8 shadow-2xl relative overflow-hidden group">
                <div className="absolute -right-20 -top-20 w-64 h-64 bg-[#d006f9]/5 rounded-full blur-3xl group-hover:bg-[#d006f9]/10 transition-colors duration-500"></div>
                
                <TrailerFilters 
                    search={search}
                    setSearch={setSearch}
                    showOnlyActive={showOnlyActive}
                    setShowOnlyActive={setShowOnlyActive}
                    isFilterOpen={isFilterOpen}
                    setIsFilterOpen={setIsFilterOpen}
                    filters={filters}
                    setFilters={setFilters}
                    viewMode={viewMode}
                    setViewMode={setViewMode}
                />

                <div className="mt-8 min-h-[400px]">
                    <TrailerTable 
                        trailers={paginatedTrailers}
                        onEdit={handleEdit}
                        onDelete={handleDelete}
                        onViewDetail={handleViewDetail}
                        loading={isLoading}
                        viewMode={viewMode}
                    />
                </div>

                {/* Pagination Controls */}
                {totalPages > 1 && (
                    <div className="mt-12 flex justify-center items-center gap-6">
                        <button
                            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                            disabled={currentPage === 1}
                            className="flex items-center gap-2 px-6 py-3 rounded-2xl bg-black/40 border border-white/5 text-white/50 hover:text-white hover:bg-black/60 transition-all disabled:opacity-30 disabled:cursor-not-allowed group font-bold text-sm shadow-[0_4px_15px_rgba(0,0,0,0.3)]"
                        >
                            <ChevronLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
                            Önceki
                        </button>
                        
                        <div className="flex items-center gap-2">
                            {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                                <button
                                    key={page}
                                    onClick={() => setCurrentPage(page)}
                                    className={cn(
                                        "w-12 h-12 rounded-2xl font-black text-sm transition-all border",
                                        currentPage === page
                                            ? "bg-[#d006f9] text-white border-[#d006f9] shadow-[0_8px_20px_rgba(208,6,249,0.3)] scale-110"
                                            : "bg-black/40 text-white/40 border-white/5 hover:bg-black/60 hover:text-white"
                                    )}
                                >
                                    {page}
                                </button>
                            ))}
                        </div>

                        <button
                            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                            disabled={currentPage === totalPages}
                            className="flex items-center gap-2 px-6 py-3 rounded-2xl bg-black/40 border border-white/5 text-white/50 hover:text-white hover:bg-black/60 transition-all disabled:opacity-30 disabled:cursor-not-allowed group font-bold text-sm shadow-[0_4px_15px_rgba(0,0,0,0.3)]"
                        >
                            Sonraki
                            <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                        </button>
                    </div>
                )}
            </div>

            {isModalOpen && (
                <TrailerModal 
                    isOpen={isModalOpen}
                    trailer={selectedTrailer}
                    onClose={() => {
                        setIsModalOpen(false)
                        setSelectedTrailer(null)
                    }}
                    onSave={async (data) => {
                        try {
                            if (selectedTrailer?.id) {
                                await dorseService.update(selectedTrailer.id, data)
                                toast.success('Dorse başarıyla güncellendi')
                            } else {
                                await dorseService.create(data as Dorse)
                                toast.success('Yeni dorse başarıyla eklendi')
                            }
                            queryClient.invalidateQueries({ queryKey: ['trailers'] })
                            setIsModalOpen(false)
                        } catch (error: any) {
                            console.error("Dorse save error:", error)
                            toast.error(error.message || 'Kayıt sırasında bir hata oluştu');
                            throw error; // Rethrow to keep modal loading state if handled inside
                        }
                    }}
                />
            )}

            {isDetailOpen && (
                <TrailerDetailModal 
                    trailer={selectedTrailer}
                    onClose={() => {
                        setIsDetailOpen(false)
                        setSelectedTrailer(null)
                    }}
                />
            )}

            <TrailerDeleteModal 
                trailer={selectedTrailer}
                isOpen={isDeleteOpen}
                onClose={() => {
                    setIsDeleteOpen(false)
                    setSelectedTrailer(null)
                }}
                onConfirm={() => selectedTrailer?.id && deleteMutation.mutate(selectedTrailer.id)}
                isDeleting={deleteMutation.isPending}
            />
        </div>
    )
}

