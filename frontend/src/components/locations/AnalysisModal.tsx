import { Modal } from '../ui/Modal';
import { RouteAnalysisCard } from './RouteAnalysisCard';
import { AnalysisResponse, Location } from '../../types/location';
import { Button } from '../ui/Button';

interface AnalysisModalProps {
    isOpen: boolean;
    onClose: () => void;
    location: Location | null;
    analysisData: AnalysisResponse | null;
    isLoading: boolean;
    onAnalyze: () => void;
}

export function AnalysisModal({ isOpen, onClose, location, analysisData, isLoading, onAnalyze }: AnalysisModalProps) {
    if (!location) return null;

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title={
                <div className="flex flex-col">
                    <span>Rota Analizi</span>
                    <span className="text-sm font-normal text-neutral-500 mt-1">
                        {location.cikis_yeri} ➝ {location.varis_yeri} ({location.mesafe_km} km)
                    </span>
                </div>
            }
            size="lg"
            className="max-w-4xl"
        >
            <div className="space-y-6">
                {isLoading ? (
                    <div className="flex flex-col items-center justify-center py-20">
                        <div className="w-16 h-16 border-4 border-primary/20 border-t-primary rounded-full animate-spin mb-4" />
                        <p className="text-neutral-500 font-medium">OpenRouteService ile analiz yapılıyor...</p>
                    </div>
                ) : analysisData && analysisData.route_analysis ? (
                    <div className="space-y-6">
                        <RouteAnalysisCard analysis={analysisData.route_analysis} />
                    </div>
                ) : (
                    <div className="text-center py-20 space-y-4">
                        <p className="text-neutral-500">Bu rota için henüz detaylı analiz yapılmamış.</p>
                        <Button onClick={onAnalyze} className="px-8 h-12 rounded-2xl">
                            Analizi Başlat
                        </Button>
                    </div>
                )}

                {/* Footer Actions */}
                <div className="pt-6 border-t border-neutral-100 flex justify-end gap-3">
                    <Button variant="secondary" onClick={onClose} className="h-12 px-6 rounded-xl">
                        Kapat
                    </Button>
                    {!isLoading && analysisData && (
                        <Button onClick={onAnalyze} className="h-12 px-6 rounded-xl">
                            Yeniden Analiz Et
                        </Button>
                    )}
                </div>
            </div>
        </Modal>
    );
}
