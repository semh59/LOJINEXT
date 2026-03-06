import { motion } from 'framer-motion'
import { LucideIcon } from 'lucide-react'
import { cn } from '../../lib/utils'

interface TripStat {
    label: string
    value: string | number
    icon: LucideIcon
    color: string
    bg: string
    unit?: string
}

interface TripStatsProps {
    stats: TripStat[]
}

const colorMap = [
    { text: 'text-[#25d1f4]', bg: 'bg-[#25d1f4]/10', border: 'border-[#25d1f4]/30', glow: 'bg-[#25d1f4]/20' }, // Primary (Cyan)
    { text: 'text-[#10b981]', bg: 'bg-[#10b981]/10', border: 'border-[#10b981]/30', glow: 'bg-[#10b981]/20' }, // Secondary (Emerald)
    { text: 'text-[#f59e0b]', bg: 'bg-[#f59e0b]/10', border: 'border-[#f59e0b]/30', glow: 'bg-[#f59e0b]/20' }, // Accent (Amber)
    { text: 'text-[#ef4444]', bg: 'bg-[#ef4444]/10', border: 'border-[#ef4444]/30', glow: 'bg-[#ef4444]/20' }, // Danger (Red)
];

export function TripStats({ stats }: TripStatsProps) {
    return (
        <div className="mb-8">
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold text-white">Sefer Özetleri</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {stats.map((stat, idx) => {
                const theme = colorMap[idx % colorMap.length];
                
                return (
                    <motion.div
                        key={idx}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: idx * 0.1 }}
                        className={cn(
                            "bg-[#132326]/60 backdrop-blur-md p-6 rounded-2xl relative overflow-hidden group border border-white/5 transition-all hover:border",
                            theme.border.replace('border-', 'hover:border-')
                        )}
                    >
                        <div className={cn(
                            "absolute -right-6 -top-6 w-24 h-24 rounded-full blur-2xl transition-all group-hover:scale-110",
                            theme.glow
                        )}></div>
                        
                        <div className="flex justify-between items-start mb-4 relative z-10">
                            <div>
                                <p className="text-slate-400 font-medium text-sm">{stat.label}</p>
                                <h3 className="text-3xl font-bold text-white mt-1">
                                    {typeof stat.value === 'number' && idx > 0 ? stat.value.toLocaleString('tr-TR') : stat.value}
                                    {stat.unit && (
                                        <span className="text-sm ml-1 text-slate-500 font-medium">
                                            {stat.unit}
                                        </span>
                                    )}
                                </h3>
                            </div>
                            <div className={cn("p-2 rounded-lg", theme.bg, theme.text)}>
                                <stat.icon className="w-6 h-6" />
                            </div>
                        </div>
                    </motion.div>
                );
            })}
            </div>
        </div>
    )
}
