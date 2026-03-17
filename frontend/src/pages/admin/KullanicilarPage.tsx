import { useQuery } from '@tanstack/react-query'
import { Card } from '@/components/ui/Card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { adminUsersApi } from '@/services/api/legacy'
import { UserPlus, Edit2 } from 'lucide-react'

export default function KullanicilarPage() {

    const { data: users = [], isLoading: loading } = useQuery({
        queryKey: ['adminUsers'],
        queryFn: () => adminUsersApi.getAll(0, 100),
        staleTime: 5 * 60 * 1000,
    })

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-primary">Kullanıcılar ve Roller</h1>
                    <p className="text-secondary mt-1">Platformdaki kullanıcıları ve yetkilerini yönetin.</p>
                </div>
                <Button variant="primary" className="flex items-center gap-2">
                    <UserPlus className="w-4 h-4" />
                    Yeni Kullanıcı
                </Button>
            </div>

            <Card padding="none">
                {loading ? (
                    <div className="flex justify-center items-center h-64">
                         <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                    </div>
                ) : (
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>E-Posta</TableHead>
                                <TableHead>Ad Soyad</TableHead>
                                <TableHead>Rol</TableHead>
                                <TableHead>Durum</TableHead>
                                <TableHead>Son Giriş</TableHead>
                                <TableHead className="text-right">İşlemler</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {users.map((user: any) => (
                                <TableRow key={user.id}>
                                    <TableCell className="font-medium">{user.email}</TableCell>
                                    <TableCell>{user.ad_soyad}</TableCell>
                                    <TableCell>
                                        <Badge variant={user.rol?.ad === 'Super Admin' ? 'warning' : 'default'}>
                                            {user.rol?.ad || 'Atanmamış'}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>
                                        <Badge variant={user.aktif ? 'success' : 'danger'} >
                                            {user.aktif ? 'Aktif' : 'Pasif'}
                                        </Badge>
                                    </TableCell>
                                    <TableCell className="text-secondary text-sm">
                                        {user.son_giris 
                                            ? new Date(user.son_giris).toLocaleDateString('tr-TR', {
                                                day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute:'2-digit'
                                            }) 
                                            : 'Hiç girmedi'}
                                    </TableCell>
                                    <TableCell className="text-right">
                                        <Button variant="outline" size="sm" className="h-8">
                                            <Edit2 className="w-4 h-4 mr-2" />
                                            Düzenle
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            ))}
                            {users.length === 0 && (
                                <TableRow>
                                    <TableCell colSpan={6} className="h-32 text-center text-secondary">
                                        Kayıtlı kullanıcı bulunamadı
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
