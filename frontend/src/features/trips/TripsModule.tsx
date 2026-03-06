import { useMemo, useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Truck, Navigation, TrendingUp, FilterX, ChevronLeft, ChevronRight } from 'lucide-react';
import { AnimatePresence } from 'framer-motion';

// API & Global State
import { tripService } from '../../services/api/trip-service';
import { useTripStore } from '../../stores/use-trip-store';
import { Trip } from '../../types';

// Modüler Bileşenler
import { TripFilters } from '../../components/trips/TripFilters';
import { TripTable } from '../../components/trips/TripTable';
import { TripFormModal } from '../../components/trips/TripFormModal';
import { TripHeader } from '../../components/trips/TripHeader';
import { TripStats } from '../../components/trips/TripStats';
import { TripAnalytics } from '../../components/trips/TripAnalytics';
import { BulkActionBar } from '../../components/trips/BulkActionBar';
import { BulkStatusModal } from '../../components/trips/BulkStatusModal';
import { BulkCancelModal } from '../../components/trips/BulkCancelModal';

import { Button } from '../../components/ui/Button';

/**
 * TripsModule - Sefer Yönetimi Ana Konteyneri
 * - Veri çekme (React Query)
 * - Mutasyonlar (Create, Update, Delete)
 * - İstatistik hesaplama
 * - Modüler bileşen orkestrasyonu
 */

export const TripsModule = () => {
    const queryClient = useQueryClient();

    // Global State (Filters & UI)
    const {
        filters,
        setFilters,
        selectedTrip,
        setSelectedTrip,
        isFormOpen,
        toggleForm,
        reset,
        selectedIds,
        toggleSelection,
        clearSelection,
        showCharts,
        toggleCharts
    } = useTripStore();

    // Cleanup & Init: Sayfaya girince ve çıkınca store'u temizle
    useEffect(() => {
        reset(); // Mount: Temiz başla
        return () => {
            reset(); // Unmount: Temiz bırak
        };
    }, [reset]);

    const [isBulkStatusOpen, setBulkStatusOpen] = useState(false);
    const [isBulkCancelOpen, setBulkCancelOpen] = useState(false);
    
    // Modal Mode State
    const [modalMode, setModalMode] = useState<{
        isReadOnly: boolean;
        initialTab: 'details' | 'timeline';
    }>({ isReadOnly: false, initialTab: 'details' });



    // 1. VERİ ÇEKME - React Query
    const { data: response, isLoading, isError } = useQuery({
        queryKey: ['trips', filters],
        queryFn: () => tripService.getAll(filters),
        staleTime: 5 * 60 * 1000, // 5 dakika cache
        refetchInterval: (query) => {
            const currentData = query.state.data as any;
            if (filters.durum === 'Devam Ediyor' || filters.durum === 'Bekliyor') {
                return 15000; // Aktif filtreliyse 15 saniyede bir
            }
            if (currentData?.items?.some((t: any) => t.durum === 'Devam Ediyor' || t.durum === 'Bekliyor')) {
                return 15000; // Listede aktif varsa 15 saniyede bir
            }
            return false;
        },
        refetchIntervalInBackground: false
    });

    const trips = response?.items || [];
    const totalCount = response?.meta?.total || 0;

    // 2. İSTATİSTİKLER - Dinamik veya MV üzerinden çekilir
    const { data: statsResponse } = useQuery({
        queryKey: ['tripStats', filters.durum, filters.baslangic_tarih, filters.bitis_tarih],
        queryFn: () => tripService.getStats({
            durum: filters.durum,
            baslangic_tarih: filters.baslangic_tarih,
            bitis_tarih: filters.bitis_tarih
        }),
        staleTime: 5 * 60 * 1000, 
    });

    const stats = useMemo(() => {
        if (!statsResponse) return [];
        
        const titlePrefix = filters.durum === 'Tamamlandı' ? 'Toplam Tamamlanan' : 'Toplam';
        
        return [
            { label: `${titlePrefix} Sefer`, value: statsResponse.toplam_sefer || 0, icon: Truck, color: 'text-[#25d1f4]', bg: 'bg-[#25d1f4]/10' },
            { label: 'Yol Karakteri', value: `%${statsResponse.avg_highway_pct || 0} Otoyol`, icon: Navigation, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
            { label: 'Toplam Tırmanış', value: ((statsResponse.total_ascent || 0) / 1000).toLocaleString('tr-TR', { minimumFractionDigits: 1, maximumFractionDigits: 1 }), unit: 'km', icon: TrendingUp, color: 'text-rose-400', bg: 'bg-rose-500/10' },
            { label: 'Toplam Tonaj', value: Math.round(statsResponse.total_weight || 0).toLocaleString('tr-TR'), unit: 'Ton', icon: Truck, color: 'text-amber-400', bg: 'bg-amber-500/10' },
        ];
    }, [statsResponse, filters.durum]);

    // 3. MUTASYONLAR

    // Create Mutation
    const createMutation = useMutation({
        mutationFn: tripService.create,
        onSuccess: (res) => {
            console.log('✅ [CREATE SUCCEEDED]:', res);
            toast.success('Yeni sefer başarıyla kaydedildi.');
            
            // Sıralama Önemli: Önce formu kapat, sonra store'u temizle (veya tam tersi)
            toggleForm(false);
            setSelectedTrip(null); 
            
            // Önbelleği temizle
            queryClient.invalidateQueries({ queryKey: ['trips'] });
            queryClient.invalidateQueries({ queryKey: ['tripStats'] });
        },
        onError: (err: any) => {
            console.error('❌ [CREATE FAILED]:', err);
            const errMsg = err?.response?.data?.detail || err?.message || 'Sefer kaydedilemedi.';
            toast.error(errMsg);
        },
    });

    // Update Mutation
    const updateMutation = useMutation({
        mutationFn: ({ id, data }: { id: number; data: Partial<Trip> }) => {
            console.log(`📡 [UPDATE] API isteği ID:${id}:`, data);
            return tripService.update(id, data);
        },
        onSuccess: (res) => {
            console.log('✅ [UPDATE SUCCEEDED]:', res);
            toast.success('Sefer bilgileri güncellendi.');
            toggleForm(false);
            queryClient.invalidateQueries({ queryKey: ['trips'] });
        },
        onError: (error: any) => {
            console.error('❌ [UPDATE FAILED]:', error);
            const errMsg = error?.response?.data?.detail || error?.message || 'Güncelleme sırasında bir hata oluştu.';
            toast.error(errMsg);
        }
    });

    // Delete Mutation
    const deleteMutation = useMutation({
        mutationFn: tripService.delete,
        onSuccess: () => {
            toast.success('Sefer silindi.');
            queryClient.invalidateQueries({ queryKey: ['trips'] });
            if (selectedTrip?.id) {
                // Form açıksa kapatılabilir veya resetlenebilir
                 toggleForm(false);
            }
        },
        onError: (error: any) => {
            const detail = error?.response?.data?.detail || 'Silme işlemi başarısız oldu.';
            if (detail.includes('foreign key constraint')) {
                toast.error('Bu sefer silinemez çünkü bağlı yakıt veya analiz verileri bulunuyor. Önce bu verileri temizlemelisiniz.');
            } else {
                toast.error(detail);
            }
        }
    });

    // Create Return Target Mutation
    const createReturnMutation = useMutation({
        mutationFn: (id: number) => tripService.createReturn(id),
        onSuccess: () => {
            toast.success('Dönüş seferi başarıyla oluşturuldu.');
            queryClient.invalidateQueries({ queryKey: ['trips'] });
        },
        onError: (error: any) => {
            const detail = error?.response?.data?.detail || 'Dönüş seferi oluşturulamadı.';
            toast.error(detail);
        }
    });

    // Bulk Mutations
    const bulkStatusMutation = useMutation({
        mutationFn: ({ ids, status }: { ids: number[]; status: string }) => 
            tripService.bulkUpdateStatus(ids, status),
        onSuccess: (res) => {
            toast.success(`${res.success_count} sefer güncellendi.`);
            if (res.failed_count > 0) toast.error(`${res.failed_count} sefer güncellenemedi.`);
            clearSelection();
            queryClient.invalidateQueries({ queryKey: ['trips'] });
            setBulkStatusOpen(false);
        }
    });

    const bulkCancelMutation = useMutation({
        mutationFn: ({ ids, reason }: { ids: number[]; reason: string }) => 
            tripService.bulkCancel(ids, reason),
        onSuccess: (res) => {
            toast.success(`${res.success_count} sefer iptal edildi.`);
            if (res.failed_count > 0) toast.error(`${res.failed_count} sefer iptal edilemedi.`);
            clearSelection();
            queryClient.invalidateQueries({ queryKey: ['trips'] });
            setBulkCancelOpen(false);
        }
    });

    const bulkDeleteMutation = useMutation({
        mutationFn: (ids: number[]) => tripService.bulkDelete(ids),
        onSuccess: (res) => {
            if (res.success_count > 0) {
                toast.success(`${res.success_count} sefer başarıyla silindi.`);
            }
            if (res.failed_count > 0) {
                toast.error(`${res.failed_count} sefer silinemedi.`);
            }
            clearSelection();
            queryClient.invalidateQueries({ queryKey: ['trips'] });
        },
        onError: (error: any) => {
            console.error('❌ [BULK DELETE FAILED]:', error);
            const errMsg = error?.response?.data?.detail || error?.message || 'Toplu silme sırasında bir hata oluştu.';
            toast.error(errMsg);
        }
    });

    // HANDLERS
    const handleFormSubmit = (data: any) => {
        // Data Transformation (Guard: Ensure numbers and data integrity)
        const payload = {
            ...data,
            arac_id: Number(data.arac_id),
            sofor_id: Number(data.sofor_id),
            dorse_id: data.dorse_id ? Number(data.dorse_id) : null,
            guzergah_id: data.guzergah_id ? Number(data.guzergah_id) : null,
            mesafe_km: Number(data.mesafe_km),
            bos_agirlik_kg: Number(data.bos_agirlik_kg || 0),
            dolu_agirlik_kg: Number(data.dolu_agirlik_kg || 0),
            net_kg: Number(data.net_kg || 0),
            is_real: true // Manual entries are always real
        };

        if (selectedTrip?.id) {
            updateMutation.mutate({ id: selectedTrip.id, data: payload });
        } else {
            createMutation.mutate(payload);
        }
    };

    const handleDelete = (trip: Trip) => {
        if (window.confirm('Bu seferi silmek istediğinize emin misiniz?')) {
            if (trip.id) deleteMutation.mutate(trip.id);
        }
    };

    const handleEdit = (trip: Trip) => {
        setModalMode({ isReadOnly: false, initialTab: 'details' });
        setSelectedTrip(trip);
        toggleForm(true);
    };

    const handleViewDetails = (trip: Trip) => {
        setModalMode({ isReadOnly: true, initialTab: 'timeline' });
        setSelectedTrip(trip);
        toggleForm(true);
    };

    const handleAdd = () => {
        setModalMode({ isReadOnly: false, initialTab: 'details' });
        setSelectedTrip(null);
        toggleForm(true);
    };



    const handleStatusChange = (trip: Trip) => {
        if (!trip.id) return;
        
        const isCancelled = trip.durum === 'İptal';
        const targetStatus = isCancelled ? 'Planlandı' : 'İptal';

        console.log(`🔄 [STATUS CHANGE] Sefer ID:${trip.id}, Mevcut Durum:${trip.durum}, Hedef Durum:${targetStatus}`);

        if (window.confirm(`Sefer durumunu '${targetStatus}' olarak değiştirmek istiyor musunuz?`)) {
            updateMutation.mutate({ 
                id: trip.id, 
                data: { durum: targetStatus } 
            });
        }
    };

    const handleExport = async () => {
        try {
            const blob = await tripService.exportExcel(filters);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `seferler_export_${new Date().getTime()}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            toast.success('Excel dosyası hazırlandı.');
        } catch (error) {
            toast.error('Dışa aktarma sırasında hata oluştu.');
        }
    };

    const handleDownloadTemplate = async () => {
        try {
            const blob = await tripService.downloadTemplate();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'sefer_yukleme_sablonu.xlsx';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            toast.success('Şablon indirildi.');
        } catch (error) {
            toast.error('Şablon indirilemedi.');
        }
    };

    const handleImport = async (file: File) => {
        try {
            const res = await tripService.uploadExcel(file);
            queryClient.invalidateQueries({ queryKey: ['trips'] });
            if (!res?.errors || res.errors.length === 0) {
                toast.success('Seferler başarıyla yüklendi.');
            }
            return res;
        } catch (error) {
            toast.error('Dosya yüklenemedi.');
            throw error;
        }
    };

    const handleCreateReturn = (trip: Trip) => {
        if (!trip.id) return;
        if (window.confirm('Bu sefer için otomatik olarak dönüş seferi oluşturulacaktır. Onaylıyor musunuz?')) {
            createReturnMutation.mutate(trip.id);
        }
    };

    return (
        <div className="flex-1 w-full h-full p-6 animate-stagger-fade overflow-y-auto custom-scrollbar">
            <TripHeader 
                onAdd={handleAdd} 
                showCharts={showCharts}
                onToggleCharts={() => toggleCharts()}
            />
            
            <TripStats stats={stats} />

            <AnimatePresence>
                {showCharts && <TripAnalytics trips={trips} />}
            </AnimatePresence>

            {/* 3. Filters Toolbar */}
            <TripFilters
                onExport={handleExport}
                onImport={handleImport}
                onDownloadTemplate={handleDownloadTemplate}
            />

            {/* 4. Data Content */}
            <div className="mt-4">
                {isError ? (
                    <div className="flex flex-col items-center justify-center p-20 glass border-rose-100 rounded-[32px]">
                        <FilterX className="w-12 h-12 text-rose-300 mb-4" />
                        <h3 className="text-lg font-bold text-rose-900 uppercase tracking-tight">Veri Yüklenemedi</h3>
                        <p className="text-rose-600 mt-1 font-medium">Lütfen internet bağlantınızı kontrol edip tekrar deneyin.</p>
                        <Button 
                            variant="secondary" 
                            className="mt-6 bg-rose-500 hover:bg-rose-600 text-white rounded-xl"
                            onClick={() => queryClient.invalidateQueries({ queryKey: ['trips'] })}
                        >
                            Yeniden Dene
                        </Button>
                    </div>
                ) : (
                    <>
                        <TripTable
                            trips={trips}
                            isLoading={isLoading}
                            onEdit={handleEdit}
                            onDelete={handleDelete}
                            onCreateReturn={handleCreateReturn}
                            onStatusChange={handleStatusChange}
                            selectedIds={selectedIds}
                            onToggleSelection={toggleSelection}
                            onViewDetails={handleViewDetails}
                        />

                        {/* Pagination Controls */}
                        {!isLoading && !isError && totalCount > 0 && (
                            <div className="flex items-center justify-between mt-6 px-4 py-3 bg-[#132326]/60 backdrop-blur-md border border-white/5 rounded-2xl">
                                <div className="text-xs font-bold text-slate-400 uppercase tracking-widest">
                                    Toplam <span className="text-[#25d1f4] ml-1">{totalCount.toLocaleString('tr-TR')}</span> Kayıt
                                </div>
                                <div className="flex items-center gap-2">
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        className="rounded-xl h-9 px-3 border-white/10 bg-[#0B1215] text-slate-400 hover:text-white transition-colors flex items-center gap-1"
                                        disabled={filters.skip === 0}
                                        onClick={() => setFilters({ skip: Math.max(0, (filters.skip || 0) - (filters.limit || 100)) })}
                                    >
                                        <ChevronLeft className="w-4 h-4" />
                                        Önceki
                                    </Button>
                                    <div className="text-xs font-bold text-white bg-white/5 px-3 py-1.5 rounded-lg border border-white/10">
                                        {Math.floor((filters.skip || 0) / (filters.limit || 100)) + 1} / {Math.ceil(totalCount / (filters.limit || 100))}
                                    </div>
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        className="rounded-xl h-9 px-3 border-white/10 bg-[#0B1215] text-slate-400 hover:text-white transition-colors flex items-center gap-1"
                                        disabled={(filters.skip || 0) + (filters.limit || 100) >= totalCount}
                                        onClick={() => setFilters({ skip: (filters.skip || 0) + (filters.limit || 100) })}
                                    >
                                        Sonraki
                                        <ChevronRight className="w-4 h-4" />
                                    </Button>
                                </div>
                            </div>
                        )}
                    </>
                )}
            </div>

            {/* 5. Form Modal */}
            <TripFormModal
                isOpen={isFormOpen}
                onClose={() => toggleForm(false)}
                initialData={selectedTrip}
                onSubmit={handleFormSubmit}
                isSubmitting={createMutation.isPending || updateMutation.isPending}
                isReadOnly={modalMode.isReadOnly}
                initialTab={modalMode.initialTab}
            />

            {/* Bulk Actions UI */}
            <BulkActionBar
                selectedCount={selectedIds.length}
                onClear={clearSelection}
                onStatusUpdate={() => setBulkStatusOpen(true)}
                onCancel={() => setBulkCancelOpen(true)}
                onDelete={() => {
                    if (window.confirm(`${selectedIds.length} seferi silmek istediğinize emin misiniz?`)) {
                        bulkDeleteMutation.mutate(selectedIds);
                    }
                }}
            />

            <BulkStatusModal
                isOpen={isBulkStatusOpen}
                onClose={() => setBulkStatusOpen(false)}
                selectedCount={selectedIds.length}
                onConfirm={(status) => bulkStatusMutation.mutate({ ids: selectedIds, status })}
                isSubmitting={bulkStatusMutation.isPending}
            />

            <BulkCancelModal
                isOpen={isBulkCancelOpen}
                onClose={() => setBulkCancelOpen(false)}
                selectedCount={selectedIds.length}
                onConfirm={(reason) => bulkCancelMutation.mutate({ ids: selectedIds, reason })}
                isSubmitting={bulkCancelMutation.isPending}
            />
        </div>
    );
};
