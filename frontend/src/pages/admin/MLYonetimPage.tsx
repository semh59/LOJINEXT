import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/Card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { adminMlApi } from '@/services/api/legacy'
import { useNotify } from '@/context/NotificationContext'
import { Play, BrainCircuit, Activity } from 'lucide-react'

export default function MLYonetimPage() {
    const [queue, setQueue] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [triggering, setTriggering] = useState(false)
    const { notify } = useNotify()

    useEffect(() => {
        loadQueue()
    }, [])

    const loadQueue = async () => {
        try {
            setLoading(true)
            const data = await adminMlApi.getQueue(50)
            setQueue(data)
        } catch (error) {
            console.error('Failed to load ML queue:', error)
            notify('error', 'Eğitim kuyruğu yüklenemedi')
        } finally {
            setLoading(false)
        }
    }

    const handleTrigger = async () => {
        // Simplified: trigger for generic vehicle 1 as demo, or prompt for vehicle ID
        try {
            setTriggering(true)
            await adminMlApi.triggerTraining(1) // hardcoded 1 for demo
            notify('success', 'Model eğitimi başlatıldı (Araç: 1)')
            loadQueue()
        } catch (error: any) {
            notify('error', error.message || 'Eğitim başlatılamadı')
        } finally {
            setTriggering(false)
        }
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-neutral-900">ML Modelleri ve Eğitim</h1>
                    <p className="text-neutral-500 mt-1">Tahmin modellerini yönetin, yeniden eğitin ve metrikleri izleyin.</p>
                </div>
                <Button 
                    variant="glossy-purple" 
                    className="flex items-center gap-2"
                    onClick={handleTrigger}
                    disabled={triggering}
                >
                    {triggering ? (
                        <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                    ) : (
                        <Play className="w-4 h-4" />
                    )}
                    Eğitimi Başlat (Araç 1)
                </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card padding="md" className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-purple-50 flex items-center justify-center shrink-0">
                        <BrainCircuit className="w-6 h-6 text-purple-500" />
                    </div>
                    <div>
                        <p className="text-sm font-bold text-neutral-500 uppercase tracking-widest">Aktif Modeller</p>
                        <p className="text-2xl font-black text-neutral-900 mt-0.5">3</p>
                    </div>
                </Card>
                <Card padding="md" className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-emerald-50 flex items-center justify-center shrink-0">
                        <Activity className="w-6 h-6 text-emerald-500" />
                    </div>
                    <div>
                        <p className="text-sm font-bold text-neutral-500 uppercase tracking-widest">Ortalama İsabet Oranı</p>
                        <p className="text-2xl font-black text-neutral-900 mt-0.5">85%</p>
                    </div>
                </Card>
            </div>

            <Card padding="none">
                <div className="p-4 border-b border-neutral-100 bg-neutral-50/50">
                    <h2 className="text-base font-bold text-neutral-800">Eğitim Kuyruğu</h2>
                </div>
                {loading ? (
                    <div className="flex justify-center items-center h-48">
                         <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                    </div>
                ) : (
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Araç ID</TableHead>
                                <TableHead>Durum</TableHead>
                                <TableHead>Algoritma / RMSE</TableHead>
                                <TableHead>Eğitim Süresi</TableHead>
                                <TableHead>Neden</TableHead>
                                <TableHead>Tarih</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {queue.map((task) => (
                                <TableRow key={task.id}>
                                    <TableCell className="font-medium">Araç #{task.arac_id}</TableCell>
                                    <TableCell>
                                        <Badge variant={
                                            task.durum === 'completed' ? 'success' :
                                            task.durum === 'failed' ? 'error' :
                                            task.durum === 'running' ? 'warning' : 'default'
                                        }>
                                            {task.durum}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>
                                        {task.metrics ? (
                                            <span className="text-xs text-neutral-600 font-medium">
                                                {task.metrics.algorithm || '-'} / {task.metrics.rmse ? task.metrics.rmse.toFixed(2) : '-'}
                                            </span>
                                        ) : '-'}
                                    </TableCell>
                                    <TableCell className="text-sm">
                                        {task.training_time_seconds ? `${task.training_time_seconds.toFixed(1)} sn` : '-'}
                                    </TableCell>
                                    <TableCell className="text-neutral-500 text-sm max-w-xs truncate" title={task.error_message || task.trigger_reason || ''}>
                                        {task.error_message || task.trigger_reason || '-'}
                                    </TableCell>
                                    <TableCell className="text-neutral-400 text-xs">
                                        {new Date(task.created_at).toLocaleString('tr-TR')}
                                    </TableCell>
                                </TableRow>
                            ))}
                            {queue.length === 0 && (
                                <TableRow>
                                    <TableCell colSpan={6} className="h-32 text-center text-neutral-500">
                                        Kuyrukta eğitim görevi yok
                                    </TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                )}
            </Card>
        </div>
    )
}
