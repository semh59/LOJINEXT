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
    ArrowLeft,
    User as UserIcon,
    Shield
} from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';
import { LojiNextLogo } from '@/components/common/LojiNextLogo';

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

  if (
    user?.role !== 'Super Admin' && 
    user?.role !== 'Admin' &&
    user?.role !== 'super_admin' &&
    user?.role !== 'admin' &&
    (user?.role as any)?.ad !== 'Super Admin' &&
    (user?.role as any)?.ad !== 'Admin'
  ) {
      return (
          <div className="flex items-center justify-center h-screen bg-base">
              <div className="bg-surface border border-border rounded-2xl shadow-sm p-10 text-center max-w-sm">
                  <div className="w-16 h-16 bg-danger/10 text-danger rounded-full flex items-center justify-center mx-auto mb-6">
                      <Shield className="w-8 h-8" />
                  </div>
                  <h1 className="text-xl font-extrabold text-primary mb-2 tracking-tight">Erişim Reddedildi</h1>
                  <p className="text-secondary text-sm mb-8">Bu alana erişim yetkiniz bulunmamaktadır.</p>
                  <Link to="/trips" className="inline-flex justify-center items-center w-full bg-accent text-accent-content font-bold py-3 rounded-xl hover:bg-accent-dark transition-all">
                      Platforma Dön
                  </Link>
              </div>
          </div>
      );
  }

  return (
    <div className="flex h-screen bg-base text-primary font-sans antialiased overflow-hidden">
      {/* Sidebar */}
      <aside className="w-[240px] bg-surface border-r border-border hidden md:flex flex-col flex-shrink-0 z-50">
        <div className="h-20 flex items-center px-6 border-b border-border">
            <Link to="/trips" className="flex items-center gap-3 group">
                <LojiNextLogo iconSize={36} textSize="text-[18px]" />
            </Link>
        </div>
        
        <nav className="flex-1 overflow-y-auto py-6 px-4 space-y-1.5 custom-scrollbar">
            {ADMIN_NAV.map((item) => {
                const isActive = item.path === '/admin' 
                    ? location.pathname === '/admin' 
                    : location.pathname.startsWith(item.path);
                    
                return (
                    <Link
                        key={item.path}
                        to={item.path}
                        className={cn(
                            "flex items-center gap-3.5 px-3 py-3 rounded-xl text-[14px] font-medium transition-all group relative",
                            isActive 
                                ? "bg-bg-elevated text-accent font-bold" 
                                : "text-secondary hover:bg-bg-elevated/50 hover:text-primary"
                        )}
                    >
                        <item.icon className={cn("w-[20px] h-[20px] shrink-0", isActive ? "text-accent" : "text-secondary group-hover:text-primary")} />
                        {item.label}
                        {isActive && (
                            <motion.div 
                                layoutId="adminActiveTab" 
                                className="absolute left-0 top-[10%] bottom-[10%] w-[3px] bg-accent rounded-r-full" 
                                transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                            />
                        )}
                    </Link>
                )
            })}
        </nav>
        
        <div className="p-6 border-t border-border space-y-3">
            <button 
                onClick={logout}
                className="flex items-center gap-3.5 text-secondary hover:text-danger w-full px-3 py-3 text-[14px] font-medium rounded-xl hover:bg-danger/10 transition-all group"
            >
                <LogOut className="w-[20px] h-[20px] text-secondary group-hover:text-danger" />
                Çıkış Yap
            </button>
            <Link 
                to="/trips" 
                className="flex items-center justify-center gap-2 w-full py-3.5 rounded-xl bg-primary hover:bg-secondary text-base font-bold text-[13px] transition-all shadow-md uppercase tracking-wider text-surface"
            >
                <ArrowLeft className="w-4 h-4" />
                Platforma Dön
            </Link>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden relative">
        {/* Header */}
        <header className="h-20 bg-surface/70 backdrop-blur-xl border-b border-border flex items-center justify-between px-8 z-30 sticky top-0">
            <div>
                 <h2 className="text-[22px] font-extrabold text-primary tracking-tight">
                    {ADMIN_NAV.find(n => location.pathname === '/admin' ? n.path === '/admin' : location.pathname.startsWith(n.path))?.label || 'Ayarlar'}
                 </h2>
            </div>
            
            <div className="flex items-center gap-5">
                <div className="flex flex-col text-right lg:flex">
                    <span className="text-sm font-bold text-primary tracking-tight mb-0.5">{user?.username}</span>
                    <span className="text-[10px] font-extrabold text-secondary uppercase tracking-widest">{user?.role}</span>
                </div>
                <div className="bg-surface border border-border shadow-sm text-accent font-bold rounded-xl size-11 flex items-center justify-center">
                    <UserIcon className="w-5 h-5" strokeWidth={2.5} />
                </div>
            </div>
        </header>

        {/* Content Area Viewport */}
        <main className="flex-1 overflow-auto p-8 bg-base relative">
            <div className="relative z-10 w-full max-w-[1280px] mx-auto">
                <Outlet />
            </div>
        </main>
      </div>
    </div>
  );
}
