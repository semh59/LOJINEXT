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
                    <span className="text-primary">Rota Analizi</span>
                    <span className="text-sm font-normal text-secondary mt-1">
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
                        <div className="w-16 h-16 border-4 border-accent/20 border-t-accent rounded-full animate-spin mb-4" />
                        <p className="text-secondary font-medium">OpenRouteService ile analiz yapılıyor...</p>
                    </div>
                ) : analysisData && analysisData.route_analysis ? (
                    <div className="space-y-6">
                        <RouteAnalysisCard analysis={analysisData.route_analysis} />
                    </div>
                ) : (
                    <div className="text-center py-20 space-y-4">
                        <p className="text-secondary">Bu rota için henüz detaylı analiz yapılmamış.</p>
                        <Button onClick={onAnalyze} className="h-10 px-8 rounded-lg font-bold">
                            Analizi Başlat
                        </Button>
                    </div>
                )}

                {/* Footer Actions */}
                <div className="pt-6 border-t border-border flex justify-end gap-3 mt-4">
                    <Button variant="secondary" onClick={onClose} className="h-10 px-6 rounded-lg">
                        Kapat
                    </Button>
                    {!isLoading && analysisData && (
                        <Button onClick={onAnalyze} className="h-10 px-6 rounded-lg">
                            Yeniden Analiz Et
                        </Button>
                    )}
                </div>
            </div>
        </Modal>
    );
}
