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
                <div className="bg-surface/90 backdrop-blur border border-border p-4 rounded-xl shadow-lg">
                    <p className="font-bold text-primary mb-2">{label}</p>
                    <div className="space-y-1 text-xs font-bold">
                        <p className="text-primary">Yakıt: {payload[0].value.toLocaleString()} ₺</p>
                        <p className="text-warning">Bakım: {payload[1].value.toLocaleString()} ₺</p>
                        <div className="h-px bg-border my-1" />
                        <p className="text-text-secondary">Toplam: {(payload[0].value + payload[1].value).toLocaleString()} ₺</p>
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
            className="w-full h-[400px] bg-surface p-6 rounded-2xl border border-border shadow-sm"
        >
            <div className="flex justify-between items-center mb-8">
                <h3 className="text-lg font-bold text-primary">Aylık Maliyet Analizi</h3>
                <div className="flex gap-4 text-xs font-bold">
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-primary" /> Yakıt
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-warning" /> Bakım
                    </div>
                </div>
            </div>

            <ResponsiveContainer width="100%" height="85%">
                <BarChart data={data} barSize={40}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
                    <XAxis
                        dataKey="month"
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: 'var(--text-secondary)', fontSize: 12, fontWeight: 600 }}
                        dy={10}
                    />
                    <YAxis
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
                        tickFormatter={(val) => `${val / 1000}k`}
                    />
                    <Tooltip content={<CustomTooltip />} cursor={{ fill: 'transparent' }} />
                    <Bar dataKey="fuel" stackId="a" fill="var(--accent)" radius={[0, 0, 4, 4]} />
                    <Bar dataKey="maintenance" stackId="a" fill="var(--warning)" radius={[4, 4, 0, 0]} />
                </BarChart>
            </ResponsiveContainer>
        </motion.div>
    )
}
