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

export default function LocationsPage() {
    // Filters & UI State
    const [search, setSearch] = useState('');
    const [zorlukFilter, setZorlukFilter] = useState<string>('');
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
        <PremiumLayout title="Aktif Rotalar & Güzergahlar" primaryColor="#ec3713">
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
                            variant="glossy-orange"
                            onClick={() => { setSelectedLocation(null); setIsFormOpen(true); }}
                            className="h-[52px] px-6"
                        >
                            <Plus className="w-5 h-5 group-hover:rotate-90 transition-transform" />
                            <span>Yeni Güzergah</span>
                        </Button>
                    </div>
                </div>

                {/* KPI Stats */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="bg-[#331e19]/70 backdrop-blur-md border border-[#482923] p-5 rounded-xl flex flex-col gap-1 relative overflow-hidden group">
                        <div className="absolute right-0 top-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                            <Activity className="w-16 h-16 text-white" />
                        </div>
                        <p className="text-[#c99b92] text-sm font-medium">Toplam Kayıtlı Rota</p>
                        <div className="flex items-end gap-3">
                            <span className="text-3xl font-bold text-white">{totalCount}</span>
                            <span className="text-emerald-500 text-sm font-bold mb-1 flex items-center">
                                <TrendingUp className="w-4 h-4 mr-1" /> 12%
                            </span>
                        </div>
                    </div>
                    <div className="bg-[#331e19]/70 backdrop-blur-md border border-[#482923] p-5 rounded-xl flex flex-col gap-1 relative overflow-hidden group">
                        <div className="absolute right-0 top-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                            <MapIcon className="w-16 h-16 text-white" />
                        </div>
                        <p className="text-[#c99b92] text-sm font-medium">Aktif Kullanımda</p>
                        <div className="flex items-end gap-3">
                            <span className="text-3xl font-bold text-white">45</span>
                            <span className="text-emerald-500 text-sm font-bold mb-1 flex items-center">
                                <TrendingUp className="w-4 h-4 mr-1" /> 5%
                            </span>
                        </div>
                    </div>
                    <div className="bg-[#331e19]/70 backdrop-blur-md border border-[#482923] p-5 rounded-xl flex flex-col gap-1 relative overflow-hidden group">
                        <div className="absolute right-0 top-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                            <Clock className="w-16 h-16 text-white" />
                        </div>
                        <p className="text-[#c99b92] text-sm font-medium">Zamanında Teslim T.</p>
                        <div className="flex items-end gap-3">
                            <span className="text-3xl font-bold text-white">94%</span>
                            <span className="text-emerald-500 text-sm font-bold mb-1 flex items-center">
                                <TrendingUp className="w-4 h-4 mr-1" /> 2%
                            </span>
                        </div>
                    </div>
                    <div className="bg-[#331e19]/70 backdrop-blur-md border border-[#482923] p-5 rounded-xl flex flex-col gap-1 relative overflow-hidden group">
                        <div className="absolute right-0 top-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                            <AlertTriangle className="w-16 h-16 text-white" />
                        </div>
                        <p className="text-[#c99b92] text-sm font-medium">Riskli Rotalar</p>
                        <div className="flex items-end gap-3">
                            <span className="text-3xl font-bold text-white">6%</span>
                            <span className="text-red-500 text-sm font-bold mb-1 flex items-center">
                                <TrendingDown className="w-4 h-4 mr-1" /> -1%
                            </span>
                        </div>
                    </div>
                </div>

                {/* Map Section */}
                <div className="relative w-full h-[350px] lg:h-[400px] rounded-xl overflow-hidden border border-[#482923] shadow-2xl">
                    <div className="absolute inset-0 bg-cover bg-center opacity-60" style={{ backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuCNX3Y9jKJjlmCevDxgWqe4hoelgOSDv6XwCB3-aHD7bkjSARKhsX-3LcrxR_3JzCGJ7-YZoClQocOFPdoOMD2fxTF9FBsAOR-t6PUwy2O6y0GqwLyeIIYjm-4RUIFFZO60MoIRNFBQyxtP3EbepaDlQ-1t1LZ6ldUqKldC703lbp1_OBWrdS8eMV3kFue3NtQ2G6MVyY8fIOxc4yzLNUJCrpf5luVhyxwXemw3xUPPn-jYjz58u84_MkSB1ebFL-GhNhCltrF10v0')" }}></div>
                    <div className="absolute inset-0 bg-gradient-to-t from-[#221411] via-[#221411]/40 to-transparent pointer-events-none"></div>
                    
                    {/* Live Tracking Label */}
                    <div className="absolute top-4 left-4 bg-[#221411]/80 backdrop-blur px-3 py-1.5 rounded-full border border-[#ec3713]/30 flex items-center gap-2 shadow-lg">
                        <span className="relative flex h-2.5 w-2.5">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#ec3713] opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-[#ec3713]"></span>
                        </span>
                        <span className="text-xs font-bold text-white uppercase tracking-wider">Canlı İzleme</span>
                    </div>

                    {/* Simulated Map Markers */}
                    <div className="absolute top-1/2 left-1/3 transform -translate-x-1/2 -translate-y-1/2">
                        <div className="relative group cursor-pointer lg:hover:scale-110 transition-transform">
                            <div className="absolute -inset-4 bg-[#ec3713]/20 rounded-full blur-md opacity-0 group-hover:opacity-100 transition-opacity"></div>
                            <MapIcon className="text-[#ec3713] w-8 h-8 drop-shadow-[0_0_8px_rgba(236,55,19,0.8)]" fill="currentColor" />
                            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 bg-[#331e19] text-white text-xs px-2 py-1 rounded border border-[#482923] whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity">
                                TR-IST-89 - Aktif Sefer
                            </div>
                        </div>
                    </div>
                </div>

                {/* Toolbar for List */}
                <div className="flex flex-col md:flex-row items-center gap-4 bg-[#331e19]/40 p-4 border border-[#482923] rounded-xl">
                    <div className="relative flex-1 group w-full">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500 group-focus-within:text-[#ec3713]" />
                        <input
                            placeholder="Şehir, bölge veya ID ara..."
                            className="w-full bg-[#221411] border border-[#482923] text-white rounded-lg py-3.5 pl-12 pr-4 focus:outline-none focus:border-[#ec3713] transition-colors placeholder-[#c99b92]"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                        />
                    </div>
                    <div className="flex items-center gap-3 w-full md:w-auto">
                        <div className="flex items-center gap-2 bg-[#221411] border border-[#482923] rounded-lg px-4 h-[52px]">
                            <Filter className="w-4 h-4 text-[#c99b92]" />
                            <select
                                className="bg-transparent border-none text-sm font-semibold text-white focus:ring-0 outline-none w-32"
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
                                "h-[52px] w-[52px] flex items-center justify-center bg-[#221411] border border-[#482923] rounded-lg hover:bg-[#331e19] transition-colors group",
                                isFetching && "opacity-50"
                            )}
                        >
                            <RefreshCw className={cn("w-5 h-5 text-[#c99b92] group-hover:text-white", isFetching && "animate-spin")} />
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
                        <div className="mt-6 p-4 border border-[#482923] rounded-xl flex items-center justify-between bg-[#331e19]/40 backdrop-blur-md">
                            <p className="text-xs text-[#c99b92]">
                                Toplam <span className="font-bold text-white">{totalCount}</span> kayıttan <span className="font-bold text-white">{Math.min(limit, locations.length)}</span> tanesi gösteriliyor
                            </p>

                            <div className="flex gap-2">
                                <button
                                    onClick={() => setPage(p => Math.max(1, p - 1))}
                                    disabled={page === 1}
                                    className="px-4 py-2 text-xs font-semibold text-[#c99b92] hover:text-white border border-[#482923] rounded-lg hover:bg-[#482923] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    Önceki
                                </button>
                                <button
                                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                                    disabled={page >= totalPages}
                                    className="px-4 py-2 text-xs font-semibold text-[#c99b92] hover:text-white border border-[#482923] rounded-lg hover:bg-[#482923] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
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
