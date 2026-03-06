import { FuelStats as IFuelStats } from '../../types'
import { Droplets, TrendingUp, Wallet, Activity } from 'lucide-react'
import { motion } from 'framer-motion'
import { cn } from '../../lib/utils'

interface FuelStatsProps {
    stats: IFuelStats
    loading: boolean
}

export function FuelStats({ stats, loading }: FuelStatsProps) {
    const formatCurrency = (val: number) =>
        new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', maximumFractionDigits: 0 }).format(val)

    const items = [
        {
            label: 'Toplam Tüketim',
            value: `${stats.total_consumption.toLocaleString()} L`,
            icon: Droplets,
            color: 'text-[#0df259]',
            bg: 'bg-[#0df259]/10'
        },
        {
            label: 'Toplam Maliyet',
            value: formatCurrency(stats.total_cost),
            icon: Wallet,
            color: 'text-[#0df259]',
            bg: 'bg-[#0df259]/10'
        },
        {
            label: 'Ortalama Tüketim',
            value: `${stats.avg_consumption.toFixed(1)} L/100km`,
            icon: Activity,
            color: 'text-white',
            bg: 'bg-white/10'
        },
        {
            label: 'Ortalama Fiyat',
            value: `${stats.avg_price.toFixed(2)} TL/L`,
            icon: TrendingUp,
            color: 'text-white',
            bg: 'bg-white/10'
        }
    ]

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {items.map((item, idx) => (
                <motion.div
                    key={idx}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.1 }}
                    className="glass-card p-6 flex flex-col justify-between flex-1 relative overflow-hidden group border border-white/5 shadow-[0_0_40px_rgba(13,242,89,0.02)]"
                >
                    <div className="absolute -right-6 -top-6 text-[#0df259]/20 opacity-5 transform rotate-12 transition-transform group-hover:scale-110">
                        <item.icon className="w-32 h-32" />
                    </div>
                    
                    <div className="relative z-10">
                        <p className="text-slate-500 text-[10px] font-bold uppercase tracking-widest mb-1">{item.label}</p>
                        {loading ? (
                            <div className="h-8 w-24 bg-white/10 animate-pulse rounded-lg mt-1" />
                        ) : (
                            <h4 className="text-3xl font-black text-white tracking-tighter drop-shadow-[0_0_10px_rgba(255,255,255,0.1)]">
                                {item.value}
                            </h4>
                        )}
                    </div>
                    
                    <div className="flex items-center gap-2 mt-4 relative z-10">
                        <div className={cn("px-2 py-1 rounded-lg text-[10px] font-black uppercase tracking-tighter flex items-center gap-1", item.bg, item.color, "border border-[#0df259]/20")}>
                            <TrendingUp className="w-3.5 h-3.5" />
                            -- %
                        </div>
                        <span className="text-slate-600 text-[10px] font-bold uppercase">geçen aya göre</span>
                    </div>
                </motion.div>
            ))}
        </div>
    )
}
