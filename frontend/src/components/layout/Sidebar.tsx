import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Briefcase,
  ArrowRightLeft,
  BookOpen,
  FileText,
  BarChart3,
  Upload,
  TrendingUp,
  Shield,
  Settings,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { useUiStore } from '../../store/uiStore';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/securities', icon: Briefcase, label: 'Titoli' },
  { to: '/transactions', icon: ArrowRightLeft, label: 'Operazioni' },
  { to: '/journal', icon: BookOpen, label: 'Scritture' },
  { to: '/documents', icon: FileText, label: 'Documenti' },
  { to: '/valuations', icon: TrendingUp, label: 'Valutazioni' },
  { to: '/reports', icon: BarChart3, label: 'Report' },
  { to: '/export', icon: Upload, label: 'Export' },
  { to: '/audit', icon: Shield, label: 'Audit Log' },
  { to: '/settings', icon: Settings, label: 'Impostazioni' },
];

export default function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useUiStore();

  return (
    <aside
      className={`fixed left-0 top-0 h-screen bg-surface border-r border-border flex flex-col z-50 transition-all duration-300 ${
        sidebarCollapsed ? 'w-16' : 'w-60'
      }`}
    >
      {/* Logo */}
      <div className="flex items-center h-16 px-4 border-b border-border">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="w-8 h-8 rounded-lg bg-primary-dim flex items-center justify-center flex-shrink-0">
            <span className="text-primary font-bold text-sm font-money">TE</span>
          </div>
          {!sidebarCollapsed && (
            <span className="font-heading text-lg text-text whitespace-nowrap">TitoliEngine</span>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 overflow-y-auto">
        <ul className="space-y-0.5 px-2">
          {navItems.map(({ to, icon: Icon, label }) => (
            <li key={to}>
              <NavLink
                to={to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                    isActive
                      ? 'sidebar-active text-primary font-medium'
                      : 'text-text-muted hover:text-text hover:bg-surface-hover'
                  }`
                }
                title={sidebarCollapsed ? label : undefined}
              >
                <Icon size={20} className="flex-shrink-0" />
                {!sidebarCollapsed && <span>{label}</span>}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Collapse toggle */}
      <button
        onClick={toggleSidebar}
        className="flex items-center justify-center h-12 border-t border-border text-text-muted hover:text-text transition-colors"
      >
        {sidebarCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
      </button>
    </aside>
  );
}
