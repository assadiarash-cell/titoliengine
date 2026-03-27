import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  ArrowRightLeft,
  BookOpen,
  Upload,
  TrendingUp,
  BarChart3,
  Shield,
  Settings,
  LogOut,
  Download,
} from 'lucide-react';
import { useAuthStore } from '../../store/authStore';

const navigation = [
  {
    section: 'PRINCIPALE',
    items: [
      { name: 'Dashboard', icon: LayoutDashboard, path: '/' },
    ],
  },
  {
    section: 'OPERATIVO',
    items: [
      { name: 'Titoli', icon: FileText, path: '/securities' },
      { name: 'Operazioni', icon: ArrowRightLeft, path: '/transactions' },
      { name: 'Scritture Contabili', icon: BookOpen, path: '/journal' },
      { name: 'Documenti', icon: Upload, path: '/documents' },
    ],
  },
  {
    section: 'CHIUSURA',
    items: [
      { name: 'Valutazioni', icon: TrendingUp, path: '/valuations' },
      { name: 'Report', icon: BarChart3, path: '/reports' },
      { name: 'Export', icon: Download, path: '/export' },
    ],
  },
  {
    section: 'SISTEMA',
    items: [
      { name: 'Audit Log', icon: Shield, path: '/audit' },
      { name: 'Impostazioni', icon: Settings, path: '/settings' },
    ],
  },
];

export default function Sidebar() {
  const location = useLocation();
  const { logout } = useAuthStore();

  return (
    <aside
      className="w-[260px] flex flex-col flex-shrink-0"
      style={{
        backgroundColor: 'var(--sidebar)',
        borderRight: '1px solid var(--border-default)',
      }}
    >
      {/* Logo */}
      <div className="h-20 flex items-center justify-center">
        <div
          className="flex items-center justify-center w-14 h-14 rounded-2xl"
          style={{
            background: 'var(--bg-primary)',
            boxShadow: 'var(--shadow-neumorphic-out)',
          }}
        >
          <span
            className="font-semibold text-xl tracking-tight"
            style={{ color: 'var(--color-primary)', fontWeight: 600 }}
          >
            TE
          </span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-4 py-6">
        {navigation.map((section, idx) => (
          <div key={section.section} className={idx > 0 ? 'mt-8' : ''}>
            <div
              className="px-3 mb-3 uppercase tracking-wider"
              style={{
                fontSize: '11px',
                fontWeight: 600,
                color: 'var(--text-tertiary)',
                letterSpacing: '0.08em',
              }}
            >
              {section.section}
            </div>
            <div className="space-y-1">
              {section.items.map((item) => {
                const isActive = location.pathname === item.path;
                const Icon = item.icon;

                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className="flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200"
                    style={{
                      background: isActive ? 'var(--bg-primary)' : 'transparent',
                      boxShadow: isActive ? 'var(--shadow-neumorphic-in)' : 'none',
                      color: isActive ? 'var(--color-primary)' : 'var(--text-secondary)',
                    }}
                    onMouseEnter={(e) => {
                      if (!isActive) {
                        e.currentTarget.style.background = 'var(--bg-elevated)';
                        e.currentTarget.style.color = 'var(--text-primary)';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isActive) {
                        e.currentTarget.style.background = 'transparent';
                        e.currentTarget.style.color = 'var(--text-secondary)';
                      }
                    }}
                  >
                    <Icon className="w-5 h-5" strokeWidth={2} />
                    <span style={{ fontSize: '15px', fontWeight: 500 }}>{item.name}</span>
                  </NavLink>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* User info */}
      <div className="p-4">
        <div
          className="flex items-center gap-3 p-3 rounded-2xl"
          style={{
            background: 'var(--bg-primary)',
            boxShadow: 'var(--shadow-neumorphic-out)',
          }}
        >
          <div
            className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0"
            style={{ backgroundColor: 'var(--color-primary)', color: 'white', fontWeight: 600, fontSize: '14px' }}
          >
            TE
          </div>
          <div className="flex-1 min-w-0">
            <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>
              TitoliEngine
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: 500 }}>
              Commercialista
            </div>
          </div>
          <button
            onClick={logout}
            className="p-2 rounded-lg transition-all duration-200"
            style={{ color: 'var(--text-secondary)' }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'var(--bg-elevated)';
              e.currentTarget.style.color = 'var(--text-primary)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'transparent';
              e.currentTarget.style.color = 'var(--text-secondary)';
            }}
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
