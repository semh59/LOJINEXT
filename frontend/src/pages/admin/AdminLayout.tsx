import { Outlet, Link, useLocation } from 'react-router-dom';
import { 
    LayoutDashboard, 
    Users, 
    Brain, 
    SlidersHorizontal, 
    Wrench, 
    Database, 
    Activity, 
    Bell,
    LogOut,
    ArrowLeft
} from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { cn } from '@/lib/utils';

const ADMIN_NAV = [
  { path: '/admin',             label: 'Genel Bakış',    icon: LayoutDashboard  },
  { path: '/admin/kullanicilar',label: 'Kullanıcılar',   icon: Users            },
  { path: '/admin/ml',          label: 'ML & Modeller',  icon: Brain            },
  { path: '/admin/konfig',      label: 'Konfigürasyon',  icon: SlidersHorizontal},
  { path: '/admin/bakim',       label: 'Bakım & Onarım', icon: Wrench           },
  { path: '/admin/veri',        label: 'Veri Yönetimi',  icon: Database         },
  { path: '/admin/saglik',      label: 'Sistem Sağlığı', icon: Activity         },
  { path: '/admin/bildirimler', label: 'Bildirimler',    icon: Bell             },
];

export default function AdminLayout() {
  const { user, logout } = useAuth();
  const location = useLocation();

  // For this local version, you might want to perform role checks
  if (
    user?.role !== 'Super Admin' && 
    user?.role !== 'Admin' &&
    user?.role !== 'super_admin' &&
    user?.role !== 'admin' &&
    (user?.role as any)?.ad !== 'Super Admin' &&
    (user?.role as any)?.ad !== 'Admin'
  ) {
      return (
          <div className="flex items-center justify-center h-screen bg-gray-50">
              <div className="text-center">
                  <h1 className="text-2xl font-bold text-red-600 mb-2">Erişim Reddedildi</h1>
                  <p className="text-gray-600">Bu sayfayı görüntüleme yetkiniz yok.</p>
                  <Link to="/trips" className="mt-4 inline-block text-primary hover:underline">
                      Ana Sayfaya Dön
                  </Link>
              </div>
          </div>
      );
  }

  return (
    <div className="flex h-screen bg-neutral-50 text-neutral-900">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-neutral-200 hidden md:flex flex-col">
        <div className="h-16 flex items-center justify-center border-b border-neutral-100">
            <span className="text-lg font-black tracking-tight text-brand-dark">
                LojiNext <span className="text-primary">Ayarlar</span>
            </span>
        </div>
        
        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1 custom-scrollbar">
            {ADMIN_NAV.map((item) => {
                const isActive = item.path === '/admin' 
                    ? location.pathname === '/admin' 
                    : location.pathname.startsWith(item.path);
                    
                return (
                    <Link
                        key={item.path}
                        to={item.path}
                        className={cn(
                            "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                            isActive 
                                ? "bg-primary/10 text-primary" 
                                : "text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900"
                        )}
                    >
                        <item.icon className="w-5 h-5 shrink-0" />
                        {item.label}
                    </Link>
                )
            })}
        </nav>
        
        <div className="p-4 border-t border-neutral-100">
            <button 
                onClick={logout}
                className="flex items-center gap-3 text-red-500 hover:text-red-700 w-full px-3 py-2 text-sm font-medium rounded-lg hover:bg-red-50 transition-colors"
            >
                <LogOut className="w-5 h-5" />
                Çıkış Yap
            </button>
            <div className="mt-4 pt-2 border-t border-neutral-100 flex justify-center">
                <Link 
                    to="/trips" 
                    className="flex items-center justify-center gap-2 w-full py-3 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold text-sm transition-all shadow-md shadow-indigo-200"
                >
                    <ArrowLeft className="w-4 h-4" />
                    Platforma Dön
                </Link>
            </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-16 bg-white border-b border-neutral-200 flex items-center justify-between px-6">
            <div>
                 <h2 className="text-lg font-bold text-neutral-800">
                    {ADMIN_NAV.find(n => location.pathname === '/admin' ? n.path === '/admin' : location.pathname.startsWith(n.path))?.label || 'Ayarlar'}
                 </h2>
            </div>
            <div className="flex items-center gap-4">
                <div className="flex flex-col text-right">
                    <span className="text-sm font-bold">{user?.username}</span>
                    <span className="text-xs text-neutral-400">{user?.role}</span>
                </div>
            </div>
        </header>

        {/* Content Area */}
        <main className="flex-1 overflow-auto p-6 bg-neutral-50/50">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
