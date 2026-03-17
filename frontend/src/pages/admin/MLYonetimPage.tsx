import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card } from '@/components/ui/Card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { adminMlApi } from '@/services/api/legacy'
import { useNotify } from '@/context/NotificationContext'
import { Play, BrainCircuit, Activity } from 'lucide-react'

export default function MLYonetimPage() {
    const queryClient = useQueryClient()
    const { notify } = useNotify()

    const { data: queue = [], isLoading: loading } = useQuery({
        queryKey: ['mlQueue'],
        queryFn: () => adminMlApi.getQueue(50),
        refetchInterval: 10000, // Poll every 10 seconds while on page
    })

    const triggerMutation = useMutation({
        mutationFn: (vehicleId: number) => adminMlApi.triggerTraining(vehicleId),
        onSuccess: () => {
            notify('success', 'Model eğitimi başlatıldı (Araç: 1)')
            queryClient.invalidateQueries({ queryKey: ['mlQueue'] })
        },
        onError: (error: any) => {
            notify('error', error.message || 'Eğitim başlatılamadı')
        }
    })

    const handleTrigger = async () => {
        triggerMutation.mutate(1)
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-primary">ML Modelleri ve Eğitim</h1>
                    <p className="text-secondary mt-1">Tahmin modellerini yönetin, yeniden eğitin ve metrikleri izleyin.</p>
                </div>
                <Button 
                    variant="primary" 
                    className="flex items-center gap-2"
                    onClick={handleTrigger}
                    disabled={triggerMutation.isPending}
                >
                    {triggerMutation.isPending ? (
                        <div className="w-4 h-4 border-2 border-bg-base/20 border-t-bg-base rounded-full animate-spin" />
                    ) : (
                        <Play className="w-4 h-4" />
                    )}
                    Eğitimi Başlat (Araç 1)
                </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card padding="md" className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center shrink-0">
                        <BrainCircuit className="w-6 h-6 text-accent" />
                    </div>
                    <div>
                        <p className="text-sm font-bold text-secondary uppercase tracking-widest">Aktif Modeller</p>
                        <p className="text-2xl font-black text-primary mt-0.5">3</p>
                    </div>
                </Card>
                <Card padding="md" className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-success/10 flex items-center justify-center shrink-0">
                        <Activity className="w-6 h-6 text-success" />
                    </div>
                    <div>
                        <p className="text-sm font-bold text-secondary uppercase tracking-widest">Ortalama İsabet Oranı</p>
                        <p className="text-2xl font-black text-primary mt-0.5">85%</p>
                    </div>
                </Card>
            </div>

            <Card padding="none">
                <div className="p-4 border-b border-border bg-bg-elevated/50">
                    <h2 className="text-base font-bold text-primary">Eğitim Kuyruğu</h2>
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
                            {queue.map((task: any) => (
                                <TableRow key={task.id}>
                                    <TableCell className="font-medium">Araç #{task.arac_id}</TableCell>
                                    <TableCell>
                                        <Badge variant={
                                            task.durum === 'completed' ? 'success' :
                                            task.durum === 'failed' ? 'danger' :
                                            task.durum === 'running' ? 'warning' : 'default'
                                        }>
                                            {task.durum}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>
                                        {task.metrics ? (
                                            <span className="text-xs text-secondary font-medium">
                                                {task.metrics.algorithm || '-'} / {task.metrics.rmse ? task.metrics.rmse.toFixed(2) : '-'}
                                            </span>
                                        ) : '-'}
                                    </TableCell>
                                    <TableCell className="text-sm">
                                        {task.training_time_seconds ? `${task.training_time_seconds.toFixed(1)} sn` : '-'}
                                    </TableCell>
                                    <TableCell className="text-secondary text-sm max-w-xs truncate" title={task.error_message || task.trigger_reason || ''}>
                                        {task.error_message || task.trigger_reason || '-'}
                                    </TableCell>
                                    <TableCell className="text-secondary text-xs">
                                        {new Date(task.created_at).toLocaleString('tr-TR')}
                                    </TableCell>
                                </TableRow>
                            ))}
                            {queue.length === 0 && (
                                <TableRow>
                                    <TableCell colSpan={6} className="h-32 text-center text-secondary">
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
