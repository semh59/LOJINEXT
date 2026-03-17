import { useEffect, useMemo, useRef, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { Truck, Navigation, TrendingUp, FilterX, ChevronLeft, ChevronRight } from 'lucide-react';
import { AnimatePresence } from 'framer-motion';
import { useSearchParams } from 'react-router-dom';

import { tripService } from '../../services/api/trip-service';
import { useTripStore } from '../../stores/use-trip-store';
import { Trip } from '../../types';

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

const STATUS_TRANSITIONS: Record<string, string[]> = {
    'Bekliyor': ['Yolda', 'Devam Ediyor', '\u0130ptal', 'Planland\u0131'],
    'Planland\u0131': ['Yolda', 'Devam Ediyor', '\u0130ptal', 'Bekliyor'],
    'Yolda': ['Tamamland\u0131', 'Tamam', '\u0130ptal'],
    'Devam Ediyor': ['Tamamland\u0131', 'Tamam', '\u0130ptal'],
    'Tamamland\u0131': [],
    'Tamam': [],
    '\u0130ptal': [],
};

export const TripsModule = () => {
    const queryClient = useQueryClient();

    const {
        filters,
        setFilters,
        selectedTrip,
        setSelectedTrip,
        isFormOpen,
        toggleForm,
        selectedIds,
        toggleSelection,
        clearSelection,
        showCharts,
        toggleCharts,
    } = useTripStore();

    const { resetFilters } = useTripStore();

    // B-005: URL Query Params Sync
    const [searchParams, setSearchParams] = useSearchParams();
    const isInitialSync = useRef(true);

    // URL → Store (on mount only)
    useEffect(() => {
        const urlDurum = searchParams.get('durum') || '';
        const urlSearch = searchParams.get('search') || '';
        const urlFrom = searchParams.get('from') || '';
        const urlTo = searchParams.get('to') || '';

        if (urlDurum || urlSearch || urlFrom || urlTo) {
            setFilters({
                durum: urlDurum,
                search: urlSearch,
                baslangic_tarih: urlFrom,
                bitis_tarih: urlTo,
            });
        }
        isInitialSync.current = false;
    }, []);

    // Store → URL (after initial sync)
    useEffect(() => {
        if (isInitialSync.current) return;
        const params = new URLSearchParams();
        if (filters.durum) params.set('durum', filters.durum);
        if (filters.search) params.set('search', filters.search);
        if (filters.baslangic_tarih) params.set('from', filters.baslangic_tarih);
        if (filters.bitis_tarih) params.set('to', filters.bitis_tarih);
        setSearchParams(params, { replace: true });
    }, [filters.durum, filters.search, filters.baslangic_tarih, filters.bitis_tarih, setSearchParams]);

    // B-002: Active filter detection
    const hasActiveFilter = Boolean(
        filters.durum || filters.search || filters.baslangic_tarih || filters.bitis_tarih
    );

    const [isBulkStatusOpen, setBulkStatusOpen] = useState(false);
    const [isBulkCancelOpen, setBulkCancelOpen] = useState(false);
    const [modalMode, setModalMode] = useState<{
        isReadOnly: boolean;
        initialTab: 'details' | 'timeline';
    }>({ isReadOnly: false, initialTab: 'details' });

    const { data: response, isLoading, isError, error } = useQuery({
        queryKey: ['trips', filters],
        queryFn: () => tripService.getAll(filters),
        staleTime: 5 * 60 * 1000,
        refetchInterval: (query) => {
            const currentData = query.state.data as any;
            if (filters.durum === 'Devam Ediyor' || filters.durum === 'Bekliyor') {
                return 15000;
            }
            if (currentData?.items?.some((t: any) => t.durum === 'Devam Ediyor' || t.durum === 'Bekliyor')) {
                return 15000;
            }
            return false;
        },
        refetchIntervalInBackground: false,
    });

    const trips = response?.items || [];
    const totalCount = response?.meta?.total || 0;
    const tripLoadErrorMessage = useMemo(() => {
        const status = (error as any)?.response?.status;
        if (status === 403) {
            return 'Seferleri goruntuleme yetkiniz bulunmuyor. Rol izinlerini kontrol edin.';
        }
        return 'Lutfen internet baglantinizi kontrol edip tekrar deneyin.';
    }, [error]);

    const { data: statsResponse } = useQuery({
        queryKey: ['tripStats', filters.durum, filters.baslangic_tarih, filters.bitis_tarih],
        queryFn: () =>
            tripService.getStats({
                durum: filters.durum,
                baslangic_tarih: filters.baslangic_tarih,
                bitis_tarih: filters.bitis_tarih,
            }),
        staleTime: 5 * 60 * 1000,
    });

    const { data: fuelPerformanceData, isLoading: isFuelPerformanceLoading } = useQuery({
        queryKey: ['tripFuelPerformance', filters],
        queryFn: () => tripService.getFuelPerformance(filters),
        enabled: showCharts,
        staleTime: 2 * 60 * 1000,
    });

    const stats = useMemo(() => {
        if (!statsResponse) return [];

        const titlePrefix =
            filters.durum === 'Tamamland\u0131' || filters.durum === 'Tamam'
                ? 'Toplam Tamamlanan'
                : 'Toplam';
        return [
            {
                label: `${titlePrefix} Sefer`,
                value: statsResponse.toplam_sefer || 0,
                icon: Truck,
                color: 'text-info',
                bg: 'bg-info/10',
            },
            {
                label: 'Yol Karakteri',
                value: `%${statsResponse.avg_highway_pct || 0} Otoyol`,
                icon: Navigation,
                color: 'text-success',
                bg: 'bg-success/10',
            },
            {
                label: 'Toplam Tirmanis',
                value: ((statsResponse.total_ascent || 0) / 1000).toLocaleString('tr-TR', {
                    minimumFractionDigits: 1,
                    maximumFractionDigits: 1,
                }),
                unit: 'km',
                icon: TrendingUp,
                color: 'text-danger',
                bg: 'bg-danger/10',
            },
            {
                label: 'Toplam Tonaj',
                value: Math.round(statsResponse.total_weight || 0).toLocaleString('tr-TR'),
                unit: 'Ton',
                icon: Truck,
                color: 'text-warning',
                bg: 'bg-warning/10',
            },
        ];
    }, [statsResponse, filters.durum]);

    const createMutation = useMutation({
        mutationFn: tripService.create,
        onSuccess: () => {
            toast.success('Yeni sefer basariyla kaydedildi.');
            toggleForm(false);
            setSelectedTrip(null);
            queryClient.invalidateQueries({ queryKey: ['trips'] });
            queryClient.invalidateQueries({ queryKey: ['tripStats'] });
        },
        onError: (err: any) => {
            toast.error(err?.response?.data?.detail || err?.message || 'Sefer kaydedilemedi.');
        },
    });

    const updateMutation = useMutation({
        mutationFn: ({ id, data }: { id: number; data: Partial<Trip> }) => tripService.update(id, data),
        onSuccess: () => {
            toast.success('Sefer bilgileri guncellendi.');
            toggleForm(false);
            queryClient.invalidateQueries({ queryKey: ['trips'] });
        },
        onError: (err: any) => {
            // B-004: Optimistic locking conflict handling
            if (err?.response?.status === 409) {
                toast.error('Bu kayıt başka biri tarafından güncellenmiş. Lütfen sayfayı yenileyip tekrar deneyin.');
            } else {
                toast.error(err?.response?.data?.detail || err?.message || 'Guncelleme sirasinda bir hata olustu.');
            }
        },
    });

    const deleteMutation = useMutation({
        mutationFn: tripService.delete,
        onSuccess: () => {
            toast.success('Sefer silindi.');
            queryClient.invalidateQueries({ queryKey: ['trips'] });
            if (selectedTrip?.id) {
                toggleForm(false);
            }
        },
        onError: (error: any) => {
            const detail = error?.response?.data?.detail || 'Silme islemi basarisiz oldu.';
            toast.error(detail);
        },
    });

    const createReturnMutation = useMutation({
        mutationFn: (id: number) => tripService.createReturn(id),
        onSuccess: () => {
            toast.success('Donus seferi basariyla olusturuldu.');
            queryClient.invalidateQueries({ queryKey: ['trips'] });
        },
        onError: (error: any) => {
            toast.error(error?.response?.data?.detail || 'Donus seferi olusturulamadi.');
        },
    });

    const bulkStatusMutation = useMutation({
        mutationFn: ({ ids, status }: { ids: number[]; status: string }) => tripService.bulkUpdateStatus(ids, status),
        onSuccess: (res) => {
            toast.success(`${res.success_count} sefer guncellendi.`);
            if (res.failed_count > 0) toast.error(`${res.failed_count} sefer guncellenemedi.`);
            clearSelection();
            queryClient.invalidateQueries({ queryKey: ['trips'] });
            setBulkStatusOpen(false);
        },
    });

    const bulkCancelMutation = useMutation({
        mutationFn: ({ ids, reason }: { ids: number[]; reason: string }) => tripService.bulkCancel(ids, reason),
        onSuccess: (res) => {
            toast.success(`${res.success_count} sefer iptal edildi.`);
            if (res.failed_count > 0) toast.error(`${res.failed_count} sefer iptal edilemedi.`);
            clearSelection();
            queryClient.invalidateQueries({ queryKey: ['trips'] });
            setBulkCancelOpen(false);
        },
    });

    const bulkDeleteMutation = useMutation({
        mutationFn: (ids: number[]) => tripService.bulkDelete(ids),
        onSuccess: (res) => {
            if (res.success_count > 0) toast.success(`${res.success_count} sefer basariyla silindi.`);
            if (res.failed_count > 0) toast.error(`${res.failed_count} sefer silinemedi.`);
            clearSelection();
            queryClient.invalidateQueries({ queryKey: ['trips'] });
        },
        onError: (err: any) => {
            toast.error(err?.response?.data?.detail || err?.message || 'Toplu silme sirasinda bir hata olustu.');
        },
    });

    const handleFormSubmit = (data: any) => {
        const payload = {
            ...data,
            arac_id: Number(data.arac_id),
            sofor_id: Number(data.sofor_id),
            dorse_id: data.dorse_id ? Number(data.dorse_id) : null,
            guzergah_id: Number(data.guzergah_id),
            mesafe_km: Number(data.mesafe_km),
            bos_agirlik_kg: Number(data.bos_agirlik_kg || 0),
            dolu_agirlik_kg: Number(data.dolu_agirlik_kg || 0),
            net_kg: Number(data.net_kg || 0),
            is_real: true,
        };

        if (selectedTrip?.id) {
            updateMutation.mutate({ 
                id: selectedTrip.id, 
                data: { ...payload, version: selectedTrip.version } 
            });
        } else {
            createMutation.mutate(payload);
        }
    };

    const handleDelete = (trip: Trip) => {
        if (window.confirm('Bu seferi silmek istediginize emin misiniz?') && trip.id) {
            deleteMutation.mutate(trip.id);
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

        const allowed = STATUS_TRANSITIONS[trip.durum] || [];
        if (allowed.length === 0) {
            toast.error(`'${trip.durum}' durumundan gecis yok.`);
            return;
        }

        const requested = window.prompt(`Yeni durum (${allowed.join(', ')}):`, allowed[0]);
        if (!requested) return;
        if (!allowed.includes(requested)) {
            toast.error('Gecersiz durum secildi.');
            return;
        }

        const payload: Partial<Trip> = { durum: requested as Trip['durum'] };
        if (requested === '\u0130ptal') {
            const reason = window.prompt('Iptal nedeni girin (min 5 karakter):', '');
            if (!reason || reason.trim().length < 5) {
                toast.error('Iptal nedeni en az 5 karakter olmalidir.');
                return;
            }
            (payload as any).iptal_nedeni = reason.trim();
        }

        updateMutation.mutate({ id: trip.id, data: payload });
    };

    const handleExport = async () => {
        const toastId = toast.loading('Excel dosyası hazırlanıyor, lütfen bekleyin...');
        try {
            const { skip, limit, ...exportFilters } = filters;
            const blob = await tripService.exportExcel(exportFilters);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `seferler_export_${new Date().getTime()}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            toast.success('Excel dosyası başarıyla indirildi.', { id: toastId });
        } catch {
            toast.error('Dışa aktarma sırasında hata oluştu.', { id: toastId });
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
            toast.success('Sablon indirildi.');
        } catch {
            toast.error('Sablon indirilemedi.');
        }
    };

    const handleImport = async (file: File) => {
        try {
            const res = await tripService.uploadExcel(file);
            queryClient.invalidateQueries({ queryKey: ['trips'] });
            if ((res.failed_count ?? 0) === 0) {
                toast.success(`${res.success_count ?? 0} sefer basariyla yuklendi.`);
            }
            return res;
        } catch (error) {
            toast.error('Dosya yuklenemedi.');
            throw error;
        }
    };

    const handleCreateReturn = (trip: Trip) => {
        if (!trip.id) return;
        if (window.confirm('Bu sefer icin otomatik donus seferi olusturulacaktir. Onayliyor musunuz?')) {
            createReturnMutation.mutate(trip.id);
        }
    };

    const pageSize = Number(filters.limit ?? 100) > 0 ? Number(filters.limit ?? 100) : 100;
    const currentSkip = Number(filters.skip ?? 0);
    const currentPage = Math.floor(currentSkip / pageSize) + 1;
    const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));

    return (
        <div className="flex-1 w-full h-full px-6 py-8 animate-stagger-fade overflow-y-auto custom-scrollbar bg-transparent">
            <TripHeader onAdd={handleAdd} showCharts={showCharts} onToggleCharts={() => toggleCharts()} />

            <TripStats stats={stats} />

            <AnimatePresence>
                {showCharts && <TripAnalytics data={fuelPerformanceData} isLoading={isFuelPerformanceLoading} />}
            </AnimatePresence>

            <TripFilters onExport={handleExport} onImport={handleImport} onDownloadTemplate={handleDownloadTemplate} />

            <div className="mt-4">
                {isError ? (
                    <div className="flex flex-col items-center justify-center p-20 bg-surface border border-danger/20 rounded-[16px]">
                        <FilterX className="w-12 h-12 text-danger/30 mb-4" />
                        <h3 className="text-lg font-bold text-primary uppercase tracking-tight">Veri Yuklenemedi</h3>
                        <p className="text-secondary mt-1 font-medium">{tripLoadErrorMessage}</p>
                        <Button
                            variant="primary"
                            className="mt-6"
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
                            hasActiveFilter={hasActiveFilter}
                            onClearFilters={resetFilters}
                        />

                        {!isLoading && !isError && totalCount > 0 && (
                            <div className="flex items-center justify-between mt-6 px-4 py-3 bg-surface border border-border rounded-[12px]">
                                <div className="text-xs font-bold text-secondary uppercase tracking-widest">
                                    Toplam <span className="text-accent ml-1">{totalCount.toLocaleString('tr-TR')}</span> Kayit
                                </div>
                                <div className="flex items-center gap-2">
                                    <Button
                                        variant="secondary"
                                        size="sm"
                                        className="h-8 shadow-none"
                                        disabled={currentSkip === 0}
                                        onClick={() => setFilters({ skip: Math.max(0, currentSkip - pageSize) })}
                                    >
                                        <ChevronLeft className="w-4 h-4" />
                                        Onceki
                                    </Button>
                                    <div className="text-xs font-bold text-primary bg-bg-elevated px-3 py-1.5 rounded-md border border-border">
                                        {currentPage} / {totalPages}
                                    </div>
                                    <Button
                                        variant="secondary"
                                        size="sm"
                                        className="h-8 shadow-none"
                                        disabled={currentSkip + pageSize >= totalCount}
                                        onClick={() => setFilters({ skip: currentSkip + pageSize })}
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

            <TripFormModal
                isOpen={isFormOpen}
                onClose={() => toggleForm(false)}
                initialData={selectedTrip}
                onSubmit={handleFormSubmit}
                isSubmitting={createMutation.isPending || updateMutation.isPending}
                isReadOnly={modalMode.isReadOnly}
                initialTab={modalMode.initialTab}
            />

            <BulkActionBar
                selectedCount={selectedIds.length}
                onClear={clearSelection}
                onStatusUpdate={() => setBulkStatusOpen(true)}
                onCancel={() => setBulkCancelOpen(true)}
                onDelete={() => {
                    if (window.confirm(`${selectedIds.length} seferi silmek istediginize emin misiniz?`)) {
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
