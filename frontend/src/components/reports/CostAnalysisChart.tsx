import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts'
import { CostAnalysis } from '../../types'
import { motion } from 'framer-motion'

interface CostAnalysisChartProps {
    data: CostAnalysis[]
}

export function CostAnalysisChart({ data }: CostAnalysisChartProps) {
    const CustomTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            return (
                <div className="bg-white/90 backdrop-blur border border-white/20 p-4 rounded-xl shadow-xl">
                    <p className="font-bold text-brand-dark mb-2">{label}</p>
                    <div className="space-y-1 text-xs font-bold">
                        <p className="text-primary">Yakıt: {payload[0].value.toLocaleString()} ₺</p>
                        <p className="text-amber-500">Bakım: {payload[1].value.toLocaleString()} ₺</p>
                        <div className="h-px bg-neutral-200 my-1" />
                        <p className="text-neutral-600">Toplam: {(payload[0].value + payload[1].value).toLocaleString()} ₺</p>
                    </div>
                </div>
            )
        }
        return null
    }

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="w-full h-[400px] glass p-6 rounded-[32px] border border-white/50"
        >
            <div className="flex justify-between items-center mb-8">
                <h3 className="text-lg font-black text-brand-dark">Aylık Maliyet Analizi</h3>
                <div className="flex gap-4 text-xs font-bold">
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-primary" /> Yakıt
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-amber-400" /> Bakım
                    </div>
                </div>
            </div>

            <ResponsiveContainer width="100%" height="85%">
                <BarChart data={data} barSize={40}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                    <XAxis
                        dataKey="month"
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: '#64748B', fontSize: 12, fontWeight: 600 }}
                        dy={10}
                    />
                    <YAxis
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: '#64748B', fontSize: 12 }}
                        tickFormatter={(val) => `${val / 1000}k`}
                    />
                    <Tooltip content={<CustomTooltip />} cursor={{ fill: 'transparent' }} />
                    <Bar dataKey="fuel" stackId="a" fill="#3B82F6" radius={[0, 0, 4, 4]} />
                    <Bar dataKey="maintenance" stackId="a" fill="#FBBF24" radius={[4, 4, 0, 0]} />
                </BarChart>
            </ResponsiveContainer>
        </motion.div>
    )
}
