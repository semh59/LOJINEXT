import { useState } from 'react';
import { MainLayout } from '../components/layout/MainLayout';
import { LocationList } from '../components/locations/LocationList';
import { LocationFormModal } from '../components/locations/LocationFormModal';
import { LocationAnalyzeModal } from '../components/locations/LocationAnalyzeModal';
import { useLocations } from '../hooks/use-locations';
import { Location, LocationCreate, LocationUpdate } from '../types/location';
import {
    Plus, Search, Filter, LayoutGrid, List,
    RefreshCw, MapIcon, ChevronLeft, ChevronRight
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { cn } from '../lib/utils';
import { motion, AnimatePresence } from 'framer-motion';

export default function LocationsPage() {
    // Filters & UI State
    const [search, setSearch] = useState('');
    const [zorlukFilter, setZorlukFilter] = useState<string>('');
    const [viewMode, setViewMode] = useState<'table' | 'grid'>('table');
    const [page, setPage] = useState(1);
    const limit = 12;

    const {
        useGetLocations,
        useCreateLocation,
        useUpdateLocation,
        useDeleteLocation
    } = useLocations({
        skip: (page - 1) * limit,
        limit: limit,
        zorluk: zorlukFilter || undefined,
        search: search || undefined
    });

    const { data: locations = [], isLoading, isFetching, refetch } = useGetLocations();
    const createMutation = useCreateLocation();
    const updateMutation = useUpdateLocation();
    const deleteMutation = useDeleteLocation();

    // Modals
    const [isFormOpen, setIsFormOpen] = useState(false);
    const [isAnalyzeOpen, setIsAnalyzeOpen] = useState(false);
    const [selectedLocation, setSelectedLocation] = useState<Location | null>(null);

    const handleEdit = (location: Location) => {
        setSelectedLocation(location);
        setIsFormOpen(true);
    };

    const handleDelete = async (location: Location) => {
        if (window.confirm(`${location.cikis_yeri} - ${location.varis_yeri} güzergahını silmek istediğinize emin misiniz?`)) {
            await deleteMutation.mutateAsync(location.id);
        }
    };

    const handleAnalyze = (location: Location) => {
        setSelectedLocation(location);
        setIsAnalyzeOpen(true);
    };

    const handleSave = async (data: LocationCreate | LocationUpdate) => {
        if (selectedLocation) {
            await updateMutation.mutateAsync({ id: selectedLocation.id, data: data as LocationUpdate });
        } else {
            await createMutation.mutateAsync(data as LocationCreate);
        }
        setIsFormOpen(false);
        setSelectedLocation(null);
    };


    return (
        <MainLayout title="Güzergah Yönetimi" breadcrumb="Sistem / Güzergahlar">
            <div className="space-y-8 pb-10">
                {/* Header Section */}
                <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6">
                    <div>
                        <h1 className="text-4xl font-black text-neutral-900 tracking-tight flex items-center gap-4">
                            Güzergahlar
                            <div className="bg-primary/10 text-primary text-[11px] font-black px-4 py-1.5 rounded-full uppercase tracking-widest border border-primary/10">
                                {locations.length} KAYITLI ROTA
                            </div>
                        </h1>
                        <p className="text-neutral-500 font-medium mt-2 max-w-lg">
                            Sık kullanılan taşıma güzergahlarını yönetin, rakım profilini analiz edin ve maliyetleri optimize edin.
                        </p>
                    </div>

                    <div className="flex flex-wrap items-center gap-3 w-full lg:w-auto">
                        <div className="flex bg-white border border-neutral-200 p-1 rounded-2xl shadow-sm">
                            <button
                                onClick={() => setViewMode('grid')}
                                className={cn(
                                    "p-2.5 rounded-xl transition-all",
                                    viewMode === 'grid' ? "bg-neutral-900 text-white shadow-lg" : "text-neutral-400 hover:text-neutral-600"
                                )}
                            >
                                <LayoutGrid className="w-5 h-5" />
                            </button>
                            <button
                                onClick={() => setViewMode('table')}
                                className={cn(
                                    "p-2.5 rounded-xl transition-all",
                                    viewMode === 'table' ? "bg-neutral-900 text-white shadow-lg" : "text-neutral-400 hover:text-neutral-600"
                                )}
                            >
                                <List className="w-5 h-5" />
                            </button>
                        </div>

                        <Button
                            onClick={() => { setSelectedLocation(null); setIsFormOpen(true); }}
                            className="h-12 px-6 rounded-2xl shadow-xl shadow-primary/20"
                        >
                            <Plus className="w-5 h-5 mr-2" />
                            Yeni Güzergah
                        </Button>
                    </div>
                </div>

                {/* Toolbar Section */}
                <div className="flex flex-col md:flex-row items-center gap-4">
                    <div className="relative flex-1 group">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400 group-focus-within:text-primary transition-colors" />
                        <Input
                            placeholder="Şehir veya bölge ara..."
                            className="pl-12 h-14 bg-white border-neutral-200 rounded-2xl shadow-sm focus:shadow-md transition-all text-base"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                        />
                    </div>

                    <div className="flex items-center gap-3 w-full md:w-auto">
                        <div className="flex items-center gap-2 bg-white border border-neutral-200 rounded-2xl px-4 h-14 shadow-sm shrink-0">
                            <Filter className="w-4 h-4 text-neutral-400" />
                            <select
                                className="bg-transparent border-none text-sm font-black text-neutral-600 focus:ring-0 outline-none uppercase tracking-wider"
                                value={zorlukFilter}
                                onChange={(e) => setZorlukFilter(e.target.value)}
                            >
                                <option value="">TÜM ZORLUKLAR</option>
                                <option value="Normal">DÜZ (NORMAL)</option>
                                <option value="Orta">EĞİMLİ (ORTA)</option>
                                <option value="Zor">DAĞLIK (ZOR)</option>
                            </select>
                        </div>

                        <button
                            onClick={() => refetch()}
                            className={cn(
                                "h-14 w-14 flex items-center justify-center bg-white border border-neutral-200 rounded-2xl shadow-sm hover:border-primary/30 transition-all group",
                                isFetching && "bg-neutral-50"
                            )}
                        >
                            <RefreshCw className={cn("w-5 h-5 text-neutral-400 group-hover:text-primary transition-all", isFetching && "animate-spin")} />
                        </button>
                    </div>
                </div>

                {/* Empty State / Content */}
                <div className="min-h-[500px] relative">
                    <AnimatePresence mode="wait">
                        <motion.div
                            key={viewMode}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            transition={{ duration: 0.3 }}
                        >
                            <LocationList
                                locations={locations}
                                loading={isLoading}
                                onEdit={handleEdit}
                                onDelete={handleDelete}
                                onAnalyze={handleAnalyze}
                                viewMode={viewMode}
                            />
                        </motion.div>
                    </AnimatePresence>

                    {/* Pagination */}
                    {locations.length > 0 && (
                        <div className="mt-12 flex flex-col md:flex-row items-center justify-between gap-6">
                            <div className="flex items-center gap-4 text-sm font-medium text-neutral-500">
                                <MapIcon className="w-5 h-5 text-neutral-300" />
                                <span>Toplam {locations.length} güzergah listeleniyor</span>
                            </div>

                            <div className="flex items-center gap-2">
                                <button
                                    onClick={() => setPage(p => Math.max(1, p - 1))}
                                    disabled={page === 1}
                                    className="w-12 h-12 flex items-center justify-center rounded-2xl bg-white border border-neutral-200 text-neutral-900 disabled:opacity-30 hover:shadow-md transition-all"
                                >
                                    <ChevronLeft className="w-5 h-5" />
                                </button>

                                <div className="flex items-center gap-1 bg-white border border-neutral-200 rounded-2xl p-1">
                                    {[1, 2, 3].map(p => (
                                        <button
                                            key={p}
                                            onClick={() => setPage(p)}
                                            className={cn(
                                                "w-10 h-10 rounded-xl text-xs font-black transition-all",
                                                page === p ? "bg-neutral-900 text-white shadow-lg" : "text-neutral-500 hover:bg-neutral-50"
                                            )}
                                        >
                                            {p}
                                        </button>
                                    ))}
                                </div>

                                <button
                                    onClick={() => setPage(p => p + 1)}
                                    className="w-12 h-12 flex items-center justify-center rounded-2xl bg-white border border-neutral-200 text-neutral-900 hover:shadow-md transition-all"
                                >
                                    <ChevronRight className="w-5 h-5" />
                                </button>
                            </div>
                        </div>
                    )}
                </div>

                {/* Modals */}
                <LocationFormModal
                    isOpen={isFormOpen}
                    onClose={() => { setIsFormOpen(false); setSelectedLocation(null); }}
                    onSave={handleSave}
                    location={selectedLocation}
                />

                <LocationAnalyzeModal
                    isOpen={isAnalyzeOpen}
                    onClose={() => { setIsAnalyzeOpen(false); setSelectedLocation(null); }}
                    location={selectedLocation}
                />
            </div>
        </MainLayout>
    );
}
