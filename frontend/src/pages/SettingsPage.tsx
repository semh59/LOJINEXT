
import { motion } from 'framer-motion'
import { MainLayout } from '../components/layout/MainLayout'
import { Shield, Bell, Database } from 'lucide-react'

export default function SettingsPage() {
    return (
        <MainLayout title="Ayarlar" breadcrumb="Sistem / Ayarlar">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-8">
                <div>
                    <h1 className="text-3xl font-black text-brand-dark">Sistem Ayarları</h1>
                    <p className="text-neutral-500 font-medium">Uygulama yapılandırması ve tercihler.</p>
                </div>

                <div className="glass rounded-3xl p-8 border border-white/50 space-y-8">

                    <div className="flex items-start gap-4">
                        <div className="p-3 bg-neutral-100 rounded-xl"><Shield className="w-6 h-6 text-neutral-600" /></div>
                        <div>
                            <h3 className="text-lg font-bold text-brand-dark">Güvenlik</h3>
                            <p className="text-neutral-500 text-sm mb-4">Şifre ve erişim politikaları.</p>
                            <button className="btn btn-secondary text-xs">Şifre Değiştir</button>
                        </div>
                    </div>

                    <div className="h-px bg-neutral-200/50" />

                    <div className="flex items-start gap-4">
                        <div className="p-3 bg-neutral-100 rounded-xl"><Bell className="w-6 h-6 text-neutral-600" /></div>
                        <div>
                            <h3 className="text-lg font-bold text-brand-dark">Bildirimler</h3>
                            <p className="text-neutral-500 text-sm mb-4">E-posta ve sistem bildirim tercihleri.</p>
                            <div className="flex items-center gap-2">
                                <span className="text-xs font-bold text-green-600 bg-green-100 px-2 py-1 rounded">Aktif</span>
                            </div>
                        </div>
                    </div>

                    <div className="h-px bg-neutral-200/50" />

                    <div className="flex items-start gap-4">
                        <div className="p-3 bg-neutral-100 rounded-xl"><Database className="w-6 h-6 text-neutral-600" /></div>
                        <div>
                            <h3 className="text-lg font-bold text-brand-dark">Veri Yönetimi</h3>
                            <p className="text-neutral-500 text-sm mb-4">Önbellek temizleme ve yedekleme.</p>
                            <button className="btn btn-secondary text-xs text-red-500 hover:text-red-600">Önbelleği Temizle</button>
                        </div>
                    </div>

                </div>
            </motion.div>
        </MainLayout>
    )
}
