import { Plus, Truck, TrendingUp } from 'lucide-react'
import { Button } from '../ui/Button'
import { cn } from '../../lib/utils'

interface TripHeaderProps {
    onAdd: () => void;
    showCharts: boolean;
    onToggleCharts: () => void;
}

export function TripHeader({ onAdd, showCharts, onToggleCharts }: TripHeaderProps) {
    return (
        <div className="flex justify-between items-center mb-6 relative z-40">
            <h1 className="text-2xl font-black text-white tracking-tight flex items-center gap-3">
                <Truck className="w-8 h-8 text-[#25d1f4]" />
                SEFER YÖNETİMİ
            </h1>

            <div className="flex items-center gap-3">
                <Button
                    onClick={onToggleCharts}
                    variant="outline"
                    size="lg"
                    className={cn(
                        "px-6 rounded-2xl border-white/10 transition-all gap-2 group/btn",
                        showCharts 
                            ? "bg-[#25d1f4] text-[#0a0f12] border-[#25d1f4] shadow-[0_0_20px_rgba(37,209,244,0.3)] font-black" 
                            : "bg-white/5 text-slate-400 hover:bg-white hover:text-[#0B1215] hover:border-white font-bold"
                    )}
                >
                    <TrendingUp className={cn(
                        "w-5 h-5 transition-colors",
                        showCharts ? "text-[#0a0f12]" : "text-slate-400 group-hover/btn:text-[#0B1215]"
                    )} />
                    {showCharts ? 'Analizi Kapat' : 'Operasyonel Analiz'}
                </Button>

                <Button 
                    onClick={onAdd}
                    variant="glossy-cyan"
                    size="lg"
                    className="px-6 rounded-2xl shadow-[0_0_20px_rgba(37,209,244,0.3)] hover:shadow-[0_0_30px_rgba(37,209,244,0.5)] transition-all"
                >
                    <Plus className="w-5 h-5 mr-1" />
                    Yeni Sefer Oluştur
                </Button>
            </div>
        </div>
    )
}
