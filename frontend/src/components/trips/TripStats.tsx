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
    { text: 'text-accent', bg: 'bg-accent/10', border: 'border-accent/30' },
    { text: 'text-success', bg: 'bg-success/10', border: 'border-success/30' },
    { text: 'text-warning', bg: 'bg-warning/10', border: 'border-warning/30' },
    { text: 'text-danger', bg: 'bg-danger/10', border: 'border-danger/30' },
];

export function TripStats({ stats }: TripStatsProps) {
    return (
        <div className="mb-8">
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-bold text-primary tracking-tight">Sefer Özetleri</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {stats.map((stat, idx) => {
                const theme = colorMap[idx % colorMap.length];
                
                return (
                    <motion.div
                        key={idx}
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6, delay: idx * 0.1, ease: "easeOut" }}
                        className={cn(
                            "bg-surface p-6 rounded-[12px] relative overflow-hidden group border border-border shadow-sm transition-all hover:shadow-md hover:border-accent/20"
                        )}
                    >
                        <div className="flex justify-between items-start mb-4 relative z-10">
                            <div>
                                <p className="text-secondary font-medium text-[13px]">{stat.label}</p>
                                <h3 className="text-2xl font-bold text-primary mt-1 tracking-tight tabular-data">
                                    {typeof stat.value === 'number' && idx > 0 ? stat.value.toLocaleString('tr-TR') : stat.value}
                                    {stat.unit && (
                                        <span className="text-xs ml-1 text-secondary font-medium uppercase tracking-wider">
                                            {stat.unit}
                                        </span>
                                    )}
                                </h3>
                            </div>
                            <div className={cn("p-2.5 rounded-lg transition-colors group-hover:bg-accent group-hover:text-bg-base", theme.bg, theme.text)}>
                                <stat.icon className="w-5 h-5" />
                            </div>
                        </div>
                    </motion.div>
                );
            })}
            </div>
        </div>
    )
}
