import { FuelStats as IFuelStats } from '../../types'
import { Droplets, TrendingUp, Wallet, Activity } from 'lucide-react'
import { motion } from 'framer-motion'

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
            color: 'bg-blue-500',
            bg: 'bg-blue-50 text-blue-700'
        },
        {
            label: 'Toplam Maliyet',
            value: formatCurrency(stats.total_cost),
            icon: Wallet,
            color: 'bg-emerald-500',
            bg: 'bg-emerald-50 text-emerald-700'
        },
        {
            label: 'Ortalama Tüketim',
            value: `${stats.avg_consumption} L/100km`,
            icon: Activity,
            color: 'bg-purple-500',
            bg: 'bg-purple-50 text-purple-700'
        },
        {
            label: 'Ortalama Fiyat',
            value: `${stats.avg_price.toFixed(2)} TL/L`,
            icon: TrendingUp,
            color: 'bg-amber-500',
            bg: 'bg-amber-50 text-amber-700'
        }
    ]

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {items.map((item, idx) => (
                <motion.div
                    key={idx}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: idx * 0.1 }}
                    className="glass p-4 rounded-2xl border border-white/50 flex items-center gap-4"
                >
                    <div className={`p-3 rounded-xl ${item.bg}`}>
                        <item.icon className="w-5 h-5" />
                    </div>
                    <div>
                        <p className="text-[10px] font-black uppercase text-neutral-400 tracking-wider font-inter">
                            {item.label}
                        </p>
                        <h3 className="text-lg font-black text-brand-dark tracking-tight">
                            {loading ? '-' : item.value}
                        </h3>
                    </div>
                </motion.div>
            ))}
        </div>
    )
}
