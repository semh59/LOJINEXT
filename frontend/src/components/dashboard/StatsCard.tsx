import { LucideIcon, ArrowUpRight, ArrowDownRight } from 'lucide-react'
import { motion } from 'framer-motion'
import CountUp from 'react-countup'
import { cn } from '../../lib/utils'

interface StatsCardProps {
    label: string
    value: string | number
    icon: LucideIcon
    trend?: string
    trendDirection?: 'up' | 'down' | 'neutral'
    iconColor?: 'blue' | 'green' | 'orange' | 'red' | 'purple'
    index?: number
    isLoading?: boolean
    suffix?: string // "km", "L", "L/100km" gibi birimler
}

const COLORS = {
    blue: { bg: 'bg-primary/10', text: 'text-primary', grad: 'from-primary/20 to-primary/5' },
    green: { bg: 'bg-success/10', text: 'text-success-dark', grad: 'from-success/20 to-success/5' },
    orange: { bg: 'bg-warning/10', text: 'text-warning-dark', grad: 'from-warning/20 to-warning/5' },
    red: { bg: 'bg-danger/10', text: 'text-danger-dark', grad: 'from-danger/20 to-danger/5' },
    purple: { bg: 'bg-purple-500/10', text: 'text-purple-600', grad: 'from-purple-500/20 to-purple-500/5' }
}

// Değerden sayısal kısmı çıkar (count-up için)
function extractNumericValue(value: string | number): { numeric: number; prefix: string; suffix: string } {
    if (typeof value === 'number') {
        return { numeric: value, prefix: '', suffix: '' }
    }

    // "-" veya boş değer için count-up yapma
    if (value === '-' || value === '') {
        return { numeric: 0, prefix: '', suffix: '' }
    }

    // "45,678 km" veya "12,345 L" formatını parse et
    const match = value.match(/^([^\d]*)([\d,\.]+)(.*)$/)
    if (match) {
        const numStr = match[2].replace(/,/g, '') // Virgülleri kaldır
        return {
            prefix: match[1].trim(),
            numeric: parseFloat(numStr) || 0,
            suffix: match[3].trim()
        }
    }

    return { numeric: 0, prefix: '', suffix: value }
}

export function StatsCard({
    label,
    value,
    icon: Icon,
    trend,
    trendDirection = 'neutral',
    iconColor = 'blue',
    index = 0,
    isLoading = false,
    suffix: propSuffix
}: StatsCardProps) {

    const TrendIcon = trendDirection === 'up' ? ArrowUpRight : trendDirection === 'down' ? ArrowDownRight : null
    const { numeric, prefix, suffix: extractedSuffix } = extractNumericValue(value)
    const displaySuffix = propSuffix || extractedSuffix

    // Sayısal değer mi kontrol et
    const shouldAnimate = numeric > 0 && !isLoading && value !== '-'

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1, duration: 0.5, ease: "easeOut" }}
            className="group card-premium p-6 flex flex-col justify-between h-full relative overflow-hidden"
        >
            {/* Background Glow */}
            <div className={cn(
                "absolute -right-4 -top-4 w-24 h-24 rounded-full blur-3xl opacity-0 group-hover:opacity-40 transition-opacity duration-500 bg-gradient-to-br",
                COLORS[iconColor].grad
            )} />

            <div className="flex items-start justify-between mb-4 relative z-10">
                <div className={cn(
                    "w-12 h-12 rounded-2xl flex items-center justify-center transition-all duration-300 group-hover:scale-110 shadow-lg",
                    COLORS[iconColor].bg,
                    COLORS[iconColor].text
                )}>
                    <Icon className="w-6 h-6" />
                </div>

                {trend && (
                    <div className={cn(
                        "px-2.5 py-1 rounded-full text-[10px] font-black tracking-wider flex items-center gap-1 uppercase",
                        trendDirection === 'up' ? "bg-success/10 text-success-dark" :
                            trendDirection === 'down' ? "bg-danger/10 text-danger-dark" :
                                "bg-neutral-100 text-neutral-500"
                    )}>
                        {TrendIcon && <TrendIcon className="w-3.5 h-3.5" />}
                        {trend}
                    </div>
                )}
            </div>

            <div className="relative z-10">
                <p className="text-[11px] font-black text-neutral-400 uppercase tracking-[0.1em] mb-1">
                    {label}
                </p>

                {isLoading ? (
                    // Skeleton loading
                    <div className="h-9 w-24 bg-neutral-200 rounded-lg animate-pulse" />
                ) : (
                    <h3 className="text-3xl font-black text-brand-dark tracking-tighter">
                        {shouldAnimate ? (
                            <>
                                {prefix}
                                <CountUp
                                    end={numeric}
                                    duration={1}
                                    separator=","
                                    decimals={numeric % 1 !== 0 ? 1 : 0}
                                    delay={index * 0.15}
                                />
                                {displaySuffix && ` ${displaySuffix}`}
                            </>
                        ) : (
                            value
                        )}
                    </h3>
                )}
            </div>

            {/* Abstract Decorative Element */}
            <div className="absolute bottom-2 right-2 opacity-10">
                <Icon className="w-12 h-12" />
            </div>
        </motion.div>
    )
}

