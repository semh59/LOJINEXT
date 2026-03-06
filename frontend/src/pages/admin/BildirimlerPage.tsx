import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/Card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { adminNotificationsApi } from '@/services/api/legacy'
import { useNotify } from '@/context/NotificationContext'
import { Bell, Plus } from 'lucide-react'

export default function BildirimlerPage() {
    const [rules, setRules] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const { notify } = useNotify()

    useEffect(() => {
        loadRules()
    }, [])

    const loadRules = async () => {
        try {
            setLoading(true)
            const data = await adminNotificationsApi.getRules()
            setRules(data)
        } catch (error) {
            console.error('Failed to load notification rules:', error)
            notify('error', 'Bildirim kuralları yüklenemedi')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-neutral-900">Bildirim Yönetimi</h1>
                    <p className="text-neutral-500 mt-1">Sistem içi bildirim ve e-posta kurallarını yapılandırın.</p>
                </div>
                <Button variant="glossy-purple" className="flex items-center gap-2">
                    <Plus className="w-4 h-4" />
                    Yeni Kural
                </Button>
            </div>

            <Card padding="none">
                <div className="p-4 border-b border-neutral-100 bg-neutral-50/50 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Bell className="w-5 h-5 text-neutral-500" />
                        <h2 className="text-base font-bold text-neutral-800">Aktif Kurallar</h2>
                    </div>
                </div>
                {loading ? (
                    <div className="flex justify-center items-center h-48">
                         <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                    </div>
                ) : (
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Olay Tipi</TableHead>
                                <TableHead>Kanallar</TableHead>
                                <TableHead>Hedef Rol ID</TableHead>
                                <TableHead>Şablon</TableHead>
                                <TableHead>Durum</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {rules.map((rule) => (
                                <TableRow key={rule.id}>
                                    <TableCell className="font-medium text-purple-700">{rule.olay_tipi}</TableCell>
                                    <TableCell>
                                        <div className="flex gap-1 flex-wrap">
                                            {rule.kanallar.map((kanal: string) => (
                                                <Badge key={kanal} variant="default" className="text-[10px] uppercase">
                                                    {kanal}
                                                </Badge>
                                            ))}
                                        </div>
                                    </TableCell>
                                    <TableCell>Rol #{rule.alici_rol_id}</TableCell>
                                    <TableCell className="text-neutral-500 max-w-xs truncate">{rule.sablon_icerik || '-'}</TableCell>
                                    <TableCell>
                                        <Badge variant={rule.aktif ? 'success' : 'default'}>
                                            {rule.aktif ? 'Aktif' : 'Pasif'}
                                        </Badge>
                                    </TableCell>
                                </TableRow>
                            ))}
                            {rules.length === 0 && (
                                <TableRow>
                                    <TableCell colSpan={5} className="h-32 text-center text-neutral-500">
                                        Bildirim kuralı bulunamadı.
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
