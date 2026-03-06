import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown } from 'lucide-react'
import { vehicleService } from '../../services/api/vehicle-service'
import { dorseService } from '../../services/dorseService'

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
        <div className={`bg-[#1a0121]/60 backdrop-blur-md p-5 rounded-2xl relative overflow-hidden group border border-[#d006f9]/20 shadow-[0_0_15px_rgba(208,6,249,0.05)] ${className}`}>
            <div className="absolute -right-4 -top-4 w-20 h-20 bg-[#d006f9]/10 rounded-full blur-2xl group-hover:bg-[#d006f9]/20 transition-colors"></div>
            <p className="text-white/60 text-xs font-medium uppercase tracking-wider mb-1">{title}</p>
            <div className="flex items-baseline gap-2">
                <span className="text-3xl font-bold text-white">{value}</span>
                {unit && <span className="text-white/60 text-sm font-medium">{unit}</span>}
                <span className={`text-xs font-bold flex items-center ml-auto ${type === 'up' ? 'text-[#0df259]' : 'text-red-400'}`}>
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
                return { total: 42, label: 'Sürücü' };
            } else {
                const res = await vehicleService.getAll({ limit: 1 });
                const total = (res as any).total ?? (Array.isArray(res) ? res.length : 0);
                return { total, label: 'Araç' };
            }
        }
    });
    
    const totalCount = countData?.total || 0;
    const unitLabel = countData?.label || 'Birim';
    const activeCount = Math.floor(totalCount * 0.85);

    if (isCountLoading) {
        return (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
                {[1,2,3].map(i => (
                    <div key={i} className="h-28 bg-[#1a0121]/40 rounded-2xl animate-pulse border border-[#d006f9]/10 shadow-[0_0_15px_rgba(208,6,249,0.05)]" />
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
                    className="border-l-4 border-l-[#d006f9]/60"
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
