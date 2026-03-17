import { useState } from 'react';
import { LocationList } from '../components/locations/LocationList';
import { LocationFormModal } from '../components/locations/LocationFormModal';
import { useLocations } from '../hooks/use-locations';
import { Location, LocationCreate, LocationUpdate, AnalysisResponse } from '../types/location';
import {
    Plus, Search, Filter, RefreshCw, MapIcon, TrendingUp, TrendingDown, Clock, Activity, AlertTriangle
} from 'lucide-react';
import { DataExportImport } from '../components/shared/DataExportImport';
import { cn } from '../lib/utils';
import { PremiumLayout } from '../components/layout/PremiumLayout';
import { motion, AnimatePresence } from 'framer-motion';

import { locationService } from '../services/api/location-service';
import { toast } from 'sonner';
import { AnalysisModal } from '../components/locations/AnalysisModal';
import { Button } from '../components/ui/Button';
import { useUrlState } from '../hooks/use-url-state';

export default function LocationsPage() {
    // Filters & UI State (Synced with URL)
    const [filters, setFilters] = useUrlState({
        search: '',
        zorluk: '',
        page: 1
    });
    const { search, zorluk: zorlukFilter, page } = filters;
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

    const { data, isLoading, isFetching, refetch } = useGetLocations();
    const locations = data?.items || [];
    const totalCount = data?.total || 0;
    const totalPages = Math.ceil(totalCount / limit);

    const createMutation = useCreateLocation();
    const updateMutation = useUpdateLocation();
    const deleteMutation = useDeleteLocation();

    // Modals
    const [isFormOpen, setIsFormOpen] = useState(false);
    const [selectedLocation, setSelectedLocation] = useState<Location | null>(null);

    // Analysis State
    const [isAnalysisOpen, setIsAnalysisOpen] = useState(false);
    const [analysisLocation, setAnalysisLocation] = useState<Location | null>(null);
    const [analysisData, setAnalysisData] = useState<AnalysisResponse | null>(null);
    const [isAnalysisLoading, setIsAnalysisLoading] = useState(false);

    const handleAnalyze = async (location: Location) => {
        setAnalysisLocation(location);
        setIsAnalysisOpen(true);
        
        // Optimistic update if data exists
        if (location.route_analysis) {
             setAnalysisData({
                 success: true,
                 api_mesafe_km: location.api_mesafe_km || 0,
                 api_sure_saat: location.api_sure_saat || 0,
                 ascent_m: location.ascent_m || 0,
                 descent_m: location.descent_m || 0,
                 elevation_profile: [], 
                 route_analysis: location.route_analysis,
                 otoban_mesafe_km: location.otoban_mesafe_km || 0,
                 sehir_ici_mesafe_km: location.sehir_ici_mesafe_km || 0
             });
        } else {
             setAnalysisData(null);
        }

        setIsAnalysisLoading(true);
        try {
            const result = await locationService.analyze(location.id);
            setAnalysisData(result);
            if(result.success) {
                toast.success('Analiz güncellendi');
                refetch();
            }
        } catch (error) {
            toast.error('Analiz yapılamadı.');
        } finally {
            setIsAnalysisLoading(false);
        }
    };


    const handleEdit = (location: Location) => {
        setSelectedLocation(location);
        setIsFormOpen(true);
    };

    const handleDelete = async (location: Location) => {
        if (window.confirm(`${location.cikis_yeri} - ${location.varis_yeri} güzergahını silmek istediğinize emin misiniz?`)) {
            await deleteMutation.mutateAsync(location.id);
        }
    };



    const handleSave = async (data: LocationCreate | LocationUpdate) => {
        try {
            if (selectedLocation) {
                await updateMutation.mutateAsync({ id: selectedLocation.id, data: data as LocationUpdate });
                toast.success('Güzergah başarıyla güncellendi.');
            } else {
                await createMutation.mutateAsync(data as LocationCreate);
                toast.success('Yeni güzergah oluşturuldu.');
            }
            setIsFormOpen(false);
            setSelectedLocation(null);
        } catch (error: any) {
            console.error(error);
             if (error.response && error.response.data && error.response.data.detail) {
                 const detail = error.response.data.detail;
                 if (Array.isArray(detail)) {
                     detail.forEach((err: any) => {
                         toast.error(`${err.loc.join('.')} : ${err.msg}`);
                     });
                 } else {
                     toast.error(typeof detail === 'string' ? detail : 'Bir hata oluştu');
                 }
             } else {
                 toast.error('İşlem başarısız oldu.');
             }
        }
    };

    const handleDownloadTemplate = async () => {
        try {
            const blob = await locationService.downloadTemplate();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'guzergah_yukleme_sablonu.xlsx';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            toast.success('Şablon indirildi.');
        } catch (error) {
            toast.error('Şablon indirilemedi.');
        }
    };

    const handleExport = async () => {
        try {
            const blob = await locationService.exportExcel();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'guzergahlar.xlsx';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            toast.success('Güzergahlar dışa aktarıldı.');
        } catch (error) {
            toast.error('Dışa aktarma başarısız.');
        }
    };

    const handleImport = async (file: File) => {
        try {
            const result = await locationService.uploadExcel(file);
            toast.success(`${result.count} güzergah başarıyla yüklendi.`);
            refetch();
        } catch (error) {
            toast.error('Dosya yüklenemedi.');
        }
    };


    return (
        <PremiumLayout title="Aktif Rotalar & Güzergahlar">
            <div className="flex-1 overflow-y-auto overflow-x-hidden p-4 lg:p-6 flex flex-col gap-6 relative z-10">
                {/* Header Action Section */}
                <div className="flex flex-col lg:flex-row items-start lg:items-center justify-end gap-4">
                    <div className="flex items-center gap-3">
                        <DataExportImport
                            variant="toolbar"
                            onImport={handleImport}
                            onExport={handleExport}
                            onDownloadTemplate={handleDownloadTemplate}
                        />
                        <Button
                            variant="primary"
                            onClick={() => { setSelectedLocation(null); setIsFormOpen(true); }}
                            className="h-[40px] px-6"
                        >
                            <Plus className="w-4 h-4 group-hover:rotate-90 transition-transform" />
                            <span>Yeni Güzergah</span>
                        </Button>
                    </div>
                </div>

                {/* KPI Stats */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="bg-surface border border-border p-5 rounded-xl flex flex-col gap-1 relative overflow-hidden group shadow-sm transition-all hover:shadow-md">
                        <div className="absolute right-0 top-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                            <Activity className="w-16 h-16 text-primary" />
                        </div>
                        <p className="text-secondary text-sm font-medium">Toplam Kayıtlı Rota</p>
                        <div className="flex items-end gap-3">
                            <span className="text-3xl font-bold text-primary">{totalCount}</span>
                            <span className="text-success text-sm font-bold mb-1 flex items-center">
                                <TrendingUp className="w-4 h-4 mr-1" /> 12%
                            </span>
                        </div>
                    </div>
                    <div className="bg-surface border border-border p-5 rounded-xl flex flex-col gap-1 relative overflow-hidden group shadow-sm transition-all hover:shadow-md">
                        <div className="absolute right-0 top-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                            <MapIcon className="w-16 h-16 text-primary" />
                        </div>
                        <p className="text-secondary text-sm font-medium">Aktif Kullanımda</p>
                        <div className="flex items-end gap-3">
                            <span className="text-3xl font-bold text-primary">45</span>
                            <span className="text-success text-sm font-bold mb-1 flex items-center">
                                <TrendingUp className="w-4 h-4 mr-1" /> 5%
                            </span>
                        </div>
                    </div>
                    <div className="bg-surface border border-border p-5 rounded-xl flex flex-col gap-1 relative overflow-hidden group shadow-sm transition-all hover:shadow-md">
                        <div className="absolute right-0 top-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                            <Clock className="w-16 h-16 text-primary" />
                        </div>
                        <p className="text-secondary text-sm font-medium">Zamanında Teslim T.</p>
                        <div className="flex items-end gap-3">
                            <span className="text-3xl font-bold text-primary">94%</span>
                            <span className="text-success text-sm font-bold mb-1 flex items-center">
                                <TrendingUp className="w-4 h-4 mr-1" /> 2%
                            </span>
                        </div>
                    </div>
                    <div className="bg-surface border border-border p-5 rounded-xl flex flex-col gap-1 relative overflow-hidden group shadow-sm transition-all hover:shadow-md">
                        <div className="absolute right-0 top-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                            <AlertTriangle className="w-16 h-16 text-primary" />
                        </div>
                        <p className="text-secondary text-sm font-medium">Riskli Rotalar</p>
                        <div className="flex items-end gap-3">
                            <span className="text-3xl font-bold text-primary">6%</span>
                            <span className="text-danger text-sm font-bold mb-1 flex items-center">
                                <TrendingDown className="w-4 h-4 mr-1" /> -1%
                            </span>
                        </div>
                    </div>
                </div>

                {/* Map Section */}
                <div className="relative w-full h-[350px] lg:h-[400px] rounded-xl overflow-hidden border border-border shadow-sm bg-bg-elevated bg-[linear-gradient(to_right,rgba(var(--secondary-rgb),0.07)_1px,transparent_1px),linear-gradient(to_bottom,rgba(var(--secondary-rgb),0.07)_1px,transparent_1px)] bg-[size:24px_24px]">
                    <div className="absolute inset-0 bg-gradient-to-t from-bg-base/80 to-transparent pointer-events-none"></div>
                    
                    {/* Live Tracking Label */}
                    <div className="absolute top-4 left-4 bg-surface px-3 py-1.5 rounded-full border border-border flex items-center gap-2 shadow-sm">
                        <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-accent"></span>
                        </span>
                        <span className="text-[10px] font-bold text-primary uppercase tracking-widest">Canlı İzleme</span>
                    </div>

                    {/* Simulated Map Markers */}
                    <div className="absolute top-1/2 left-1/3 transform -translate-x-1/2 -translate-y-1/2">
                        <div className="relative group cursor-pointer lg:hover:scale-110 transition-transform">
                            <div className="absolute -inset-4 bg-accent/20 rounded-full blur-md opacity-0 group-hover:opacity-100 transition-opacity"></div>
                            <MapIcon className="text-accent w-8 h-8 drop-shadow-sm" fill="currentColor" />
                            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 bg-surface text-primary text-xs px-2 py-1 rounded border border-border whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity">
                                TR-IST-89 - Aktif Sefer
                            </div>
                        </div>
                    </div>
                </div>

                {/* Toolbar for List */}
                <div className="flex flex-col md:flex-row items-center gap-4 bg-surface p-4 border border-border rounded-xl">
                    <div className="relative flex-1 group w-full">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-secondary group-focus-within:text-accent transition-colors" />
                        <input
                            placeholder="Şehir, bölge veya ID ara..."
                            className="w-full h-10 bg-bg-elevated border border-border text-primary rounded-lg pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-accent/20 transition-all placeholder:text-secondary font-medium"
                            value={search}
                            onChange={(e) => setFilters({ search: e.target.value, page: 1 })}
                        />
                    </div>
                    <div className="flex items-center gap-3 w-full md:w-auto">
                        <div className="flex items-center gap-2 bg-bg-elevated border border-border rounded-lg px-3 h-10 w-full md:w-auto hover:border-accent/30 transition-colors">
                            <Filter className="w-4 h-4 text-secondary" />
                            <select
                                className="bg-transparent border-none text-xs font-bold text-primary focus:ring-0 outline-none w-32 appearance-none uppercase tracking-tight"
                                value={zorlukFilter}
                                onChange={(e) => setFilters({ zorluk: e.target.value, page: 1 })}
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
                                "h-10 w-10 flex items-center justify-center bg-bg-elevated border border-border rounded-lg hover:border-accent/30 transition-all group active:scale-95",
                                isFetching && "opacity-50"
                            )}
                        >
                            <RefreshCw className={cn("w-4 h-4 text-secondary group-hover:text-accent transition-colors", isFetching && "animate-spin")} />
                        </button>
                    </div>
                </div>

                {/* Empty State / Content */}
                <div className="min-h-[500px] relative">
                    <AnimatePresence mode="wait">
                        <motion.div
                            key="table-view"
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
                                onAdd={() => { setSelectedLocation(null); setIsFormOpen(true); }}
                                viewMode="table"
                            />
                        </motion.div>
                    </AnimatePresence>

                    {/* Pagination */}
                    {locations.length > 0 && (
                        <div className="mt-6 p-4 border border-border rounded-xl flex items-center justify-between bg-surface shadow-sm">
                            <p className="text-xs text-secondary">
                                Toplam <span className="font-bold text-primary">{totalCount}</span> kayıttan <span className="font-bold text-primary">{Math.min(limit, locations.length)}</span> tanesi gösteriliyor
                            </p>

                            <div className="flex gap-2">
                                <button
                                    onClick={() => setFilters({ page: Math.max(1, page - 1) })}
                                    disabled={page === 1}
                                    className="px-4 py-2 text-xs font-semibold text-secondary hover:text-primary border border-border rounded-lg hover:bg-bg-elevated transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    Önceki
                                </button>
                                <button
                                    onClick={() => setFilters({ page: Math.min(totalPages, page + 1) })}
                                    disabled={page >= totalPages}
                                    className="px-4 py-2 text-xs font-semibold text-secondary hover:text-primary border border-border rounded-lg hover:bg-bg-elevated transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    Sonraki
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
                
                <AnalysisModal
                    isOpen={isAnalysisOpen}
                    onClose={() => { setIsAnalysisOpen(false); setAnalysisLocation(null); }}
                    location={analysisLocation}
                    analysisData={analysisData}
                    isLoading={isAnalysisLoading}
                    onAnalyze={() => analysisLocation && handleAnalyze(analysisLocation)}
                />
            </div>
        </PremiumLayout>
    );
}
