import { FileText, Truck, Users, Download, ArrowRight } from 'lucide-react'
import { motion } from 'framer-motion'
import { Button } from '../ui/Button'

interface ReportCardProps {
    onDownload: (type: string) => Promise<void>
}

export function ReportCards({ onDownload }: ReportCardProps) {
    const cards = [
        {
            id: 'fleet_summary',
            title: 'Filo Özeti',
            desc: 'Genel filo performansı, yakıt ve maliyet özeti.',
            icon: FileText,
            color: 'bg-blue-100 text-blue-600',
            grad: 'from-blue-500/10 to-blue-500/5'
        },
        {
            id: 'vehicle_detail',
            title: 'Araç Detay Raporu',
            desc: 'Seçili araçlar için sefer ve tüketim detayları.',
            icon: Truck,
            color: 'bg-purple-100 text-purple-600',
            grad: 'from-purple-500/10 to-purple-500/5'
        },
        {
            id: 'driver_comparison',
            title: 'Sürücü Karşılaştırma',
            desc: 'Sürücü puanları ve ihlal analizleri.',
            icon: Users,
            color: 'bg-emerald-100 text-emerald-600',
            grad: 'from-emerald-500/10 to-emerald-500/5'
        }
    ]

    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {cards.map((card, i) => (
                <motion.div
                    key={card.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.1 }}
                    className={`relative overflow-hidden glass p-6 rounded-[32px] border border-white/50 group hover:shadow-lg transition-all`}
                >
                    <div className={`absolute inset-0 bg-gradient-to-br ${card.grad} opacity-0 group-hover:opacity-100 transition-opacity`} />

                    <div className="relative z-10">
                        <div className={`w-14 h-14 ${card.color} rounded-2xl flex items-center justify-center mb-6 shadow-sm`}>
                            <card.icon className="w-7 h-7" />
                        </div>

                        <h3 className="text-xl font-bold text-brand-dark mb-2">{card.title}</h3>
                        <p className="text-neutral-500 text-sm font-medium mb-8 leading-relaxed h-[40px]">
                            {card.desc}
                        </p>

                        <Button
                            variant="secondary"
                            className="w-full justify-between group-hover:bg-white transition-all shadow-sm"
                            onClick={() => onDownload(card.id)}
                        >
                            <span className="flex items-center gap-2">
                                <Download className="w-4 h-4" />
                                PDF İndir
                            </span>
                            <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 -translate-x-2 group-hover:translate-x-0 transition-all" />
                        </Button>
                    </div>
                </motion.div>
            ))}
        </div>
    )
}
