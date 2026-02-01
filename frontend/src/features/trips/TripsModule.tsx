import { useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { toast } from 'sonner';
import { Truck, Navigation, Weight, TrendingUp, FilterX } from 'lucide-react';

// API & Global State
import { tripService } from '../../services/api/trip-service';
import { useTripStore } from '../../stores/use-trip-store';
import { Trip } from '../../types';

// Modüler Bileşenler
import { TripFilters } from '../../components/trips/TripFilters';
import { TripTable } from '../../components/trips/TripTable';
import { TripFormModal } from '../../components/trips/TripFormModal';
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
        selectedTrip,
        setSelectedTrip,
        isFormOpen,
        toggleForm
    } = useTripStore();

    // 1. VERİ ÇEKME - React Query
    const { data: trips = [], isLoading, isError } = useQuery({
        queryKey: ['trips', filters],
        queryFn: () => tripService.getAll(filters),
        staleTime: 5 * 60 * 1000, // 5 dakika cache
    });

    // 2. İSTATİSTİKLER - useMemo ile optimize
    const stats = useMemo(() => {
        const totalTrips = trips.length;
        const totalKm = trips.reduce((acc, curr) => acc + (curr.mesafe_km || 0), 0);
        const totalTon = trips.reduce((acc, curr) => acc + (curr.ton || (curr.net_kg / 1000) || 0), 0);
        const activeTrips = trips.filter(t => t.durum === 'Devam Ediyor' || t.durum === 'Yolda').length;

        return [
            { label: 'Toplam Sefer', value: totalTrips, icon: Truck, color: 'text-indigo-600', bg: 'bg-indigo-50' },
            { label: 'Toplam Mesafe', value: `${totalKm.toLocaleString('tr-TR')} km`, icon: Navigation, color: 'text-emerald-600', bg: 'bg-emerald-50' },
            { label: 'Taşınan Yük', value: `${totalTon.toFixed(1)} ton`, icon: Weight, color: 'text-amber-600', bg: 'bg-amber-50' },
            { label: 'Aktif / Yolda', value: activeTrips, icon: TrendingUp, color: 'text-rose-600', bg: 'bg-rose-50' },
        ];
    }, [trips]);

    // 3. MUTASYONLAR

    // Create Mutation with Optimistic Updates
    const createMutation = useMutation({
        mutationFn: tripService.create,
        onMutate: async (newTrip) => {
            await queryClient.cancelQueries({ queryKey: ['trips', filters] });
            const previousTrips = queryClient.getQueryData(['trips', filters]);

            // Fake optimistic trip
            const optimisticTrip = { ...newTrip, id: Math.random(), durum: newTrip.durum || 'Tamam' };

            queryClient.setQueryData(['trips', filters], (old: any) => [optimisticTrip, ...(old || [])]);
            return { previousTrips };
        },
        onError: (_err, _, context) => {
            queryClient.setQueryData(['trips', filters], context?.previousTrips);
            toast.error('Sefer oluşturulurken hata meydana geldi.');
        },
        onSuccess: () => {
            toast.success('Yeni sefer başarıyla kaydedildi.');
            toggleForm(false);
            queryClient.invalidateQueries({ queryKey: ['trips'] });
        },
    });

    // Update Mutation
    const updateMutation = useMutation({
        mutationFn: ({ id, data }: { id: number; data: Partial<Trip> }) => tripService.update(id, data),
        onSuccess: () => {
            toast.success('Sefer bilgileri güncellendi.');
            toggleForm(false);
            queryClient.invalidateQueries({ queryKey: ['trips'] });
        },
    });

    // Delete Mutation
    const deleteMutation = useMutation({
        mutationFn: tripService.delete,
        onSuccess: () => {
            toast.success('Sefer silindi.');
            queryClient.invalidateQueries({ queryKey: ['trips'] });
        },
    });

    // HANDLERS
    const handleFormSubmit = (data: any) => {
        if (selectedTrip?.id) {
            updateMutation.mutate({ id: selectedTrip.id, data });
        } else {
            createMutation.mutate(data);
        }
    };

    const handleEdit = (trip: Trip) => {
        setSelectedTrip(trip);
        toggleForm(true);
    };

    const handleDelete = (id: number) => {
        if (confirm('Bu sefer kaydını silmek istediğinize emin misiniz?')) {
            deleteMutation.mutate(id);
        }
    };

    const handleExport = async () => {
        try {
            const blob = await tripService.exportExcel(filters);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `seferler_export_${new Date().getTime()}.xlsx`;
            a.click();
            toast.success('Excel dosyası hazırlandı.');
        } catch (error) {
            toast.error('Dışa aktarma sırasında hata oluştu.');
        }
    };

    return (
        <div className="space-y-8 pb-10">
            {/* 1. Header & Stats Section */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {stats.map((stat, idx) => (
                    <motion.div
                        key={stat.label}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: idx * 0.1 }}
                        className="bg-white/70 backdrop-blur-sm p-6 rounded-[32px] border border-slate-200/60 shadow-sm flex items-center justify-between group hover:shadow-lg transition-all"
                    >
                        <div>
                            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">{stat.label}</p>
                            <h3 className="text-2xl font-black text-slate-900 mt-1 tabular-nums tracking-tight">
                                {stat.value}
                            </h3>
                        </div>
                        <div className={`p-4 rounded-2xl ${stat.bg} group-hover:scale-110 transition-transform`}>
                            <stat.icon className={`w-6 h-6 ${stat.color}`} />
                        </div>
                    </motion.div>
                ))}
            </div>

            {/* 2. Filter Toolbar */}
            <TripFilters
                onExport={handleExport}
                onAdd={() => toggleForm(true)}
            />

            {/* 3. Data Table Section */}
            <div className="space-y-4">
                {isError ? (
                    <div className="flex flex-col items-center justify-center p-20 bg-rose-50 rounded-[32px] border border-rose-100">
                        <FilterX className="w-12 h-12 text-rose-300 mb-4" />
                        <h3 className="text-lg font-bold text-rose-900">Veri Yüklenemedi</h3>
                        <p className="text-rose-600 mt-1">Sunucuyla bağlantı kurulurken hata oluştu.</p>
                        <Button variant="outline" className="mt-6 font-bold" onClick={() => queryClient.invalidateQueries({ queryKey: ['trips'] })}>
                            Yeniden Dene
                        </Button>
                    </div>
                ) : (
                    <TripTable
                        trips={trips}
                        isLoading={isLoading}
                        onEdit={handleEdit}
                        onDelete={handleDelete}
                    />
                )}
            </div>

            {/* 4. Form Modal */}
            <TripFormModal
                isOpen={isFormOpen}
                onClose={() => toggleForm(false)}
                initialData={selectedTrip}
                onSubmit={handleFormSubmit}
                isSubmitting={createMutation.isPending || updateMutation.isPending}
            />
        </div>
    );
};
