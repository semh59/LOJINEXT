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
            <h1 className="text-2xl font-black text-primary tracking-tight flex items-center gap-3">
                <Truck className="w-8 h-8 text-accent" />
                SEFER YÖNETİMİ
            </h1>

            <div className="flex items-center gap-3">
                <Button
                    onClick={onToggleCharts}
                    variant="outline"
                    size="lg"
                    className={cn(
                        "px-6 rounded-2xl border-border transition-all gap-2 group/btn",
                        showCharts 
                            ? "bg-accent text-bg-base border-accent shadow-lg shadow-accent/20 font-black" 
                            : "bg-surface text-secondary hover:bg-bg-elevated hover:text-primary hover:border-border font-bold"
                    )}
                >
                    <TrendingUp className={cn(
                        "w-5 h-5 transition-colors",
                        showCharts ? "text-bg-base" : "text-secondary group-hover/btn:text-primary"
                    )} />
                    {showCharts ? 'Paneli Kapat' : 'Yakit Performansi'}
                </Button>

                <Button 
                    onClick={onAdd}
                    variant="primary"
                    size="lg"
                    className="px-6 rounded-2xl shadow-lg shadow-accent/20 hover:shadow-accent/40 transition-all"
                >
                    <Plus className="w-5 h-5 mr-1" />
                    Yeni Sefer Oluştur
                </Button>
            </div>
        </div>
    )
}
