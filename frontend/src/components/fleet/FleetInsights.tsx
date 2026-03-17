import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown } from 'lucide-react'
import { vehicleService } from '../../services/api/vehicle-service'
import { dorseService } from '../../services/dorseService'
import { cn } from '../../lib/utils'

interface StatProps {
    title: string
    value: string
    unit?: string
    trend: number
    type: 'up' | 'down'
    className?: string
}

function StatCard({ title, value, unit, trend, type, className = '' }: StatProps) {
    return (
        <div className={cn(
            "bg-surface p-5 rounded-[12px] relative overflow-hidden group border border-border shadow-sm transition-all hover:shadow-md",
            className
        )}>
            <p className="text-secondary text-[11px] font-bold uppercase tracking-widest mb-1">{title}</p>
            <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-primary tracking-tight">{value}</span>
                {unit && <span className="text-secondary text-sm font-medium">{unit}</span>}
                <span className={cn(
                    "text-xs font-bold flex items-center ml-auto",
                    type === 'up' ? 'text-success' : 'text-danger'
                )}>
                    {type === 'up' ? <TrendingUp className="w-3.5 h-3.5 mr-1" /> : <TrendingDown className="w-3.5 h-3.5 mr-1" />}
                    {trend}%
                </span>
            </div>
        </div>
    )
}

export function FleetInsights({ activeTab = 'vehicles' }: { activeTab?: string }) {
    const { data: countData, isLoading: isCountLoading } = useQuery({
        queryKey: ['fleet-counts', activeTab],
        queryFn: async () => {
            if (activeTab === 'trailers') {
                const res = await dorseService.getAll({ limit: 1 });
                const total = (res as any).total ?? (Array.isArray(res) ? res.length : 0);
                return { total, label: 'Dorse' };
            } else if (activeTab === 'drivers') {
                const { driverService } = await import('../../services/api/driver-service');
                const res = await driverService.getAll({ limit: 1 });
                return { total: res.total, label: 'Sürücü' };
            } else {
                const res = await vehicleService.getAll({ limit: 1 });
                const total = (res as any).total ?? (Array.isArray(res) ? res.length : 0);
                return { total, label: 'Araç' };
            }
        }
    });
    
    const totalCount = countData?.total || 0;
    const unitLabel = countData?.label || 'Birim';
    const activeCount = totalCount; // Using real total instead of 85% estimation

    if (isCountLoading) {
        return (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
                {[1,2,3].map(i => (
                    <div key={i} className="h-28 bg-bg-elevated/50 rounded-[12px] animate-pulse border border-border" />
                ))}
            </div>
        )
    }

    return (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-2">
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0 }}>
                <StatCard 
                    title={`Toplam ${unitLabel}`} 
                    value={totalCount.toString()} 
                    trend={5} 
                    type="up" 
                />
            </motion.div>
            
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
                <StatCard 
                    title={`Aktif ${unitLabel}lar`} 
                    value={activeCount.toString()} 
                    trend={2} 
                    type="up" 
                    className="border-l-[3px] border-l-accent/60"
                />
            </motion.div>

            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
                <StatCard 
                    title="Aylık Ort. Verimlilik" 
                    value="%94" 
                    trend={4} 
                    type="up" 
                />
            </motion.div>
        </div>
    )
}
