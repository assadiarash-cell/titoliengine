import { useLocation } from 'react-router-dom';
import { ChevronRight, LogOut, Bell } from 'lucide-react';
import { useAuthStore } from '../../store/authStore';

const routeNames: Record<string, string> = {
  '/': 'Dashboard',
  '/securities': 'Titoli',
  '/transactions': 'Operazioni',
  '/journal': 'Scritture Contabili',
  '/documents': 'Documenti',
  '/valuations': 'Valutazioni',
  '/reports': 'Report',
  '/export': 'Export',
  '/audit': 'Audit Log',
  '/settings': 'Impostazioni',
};

export default function Header() {
  const location = useLocation();
  const { logout } = useAuthStore();

  const pathSegments = location.pathname.split('/').filter(Boolean);
  const currentRoute = '/' + (pathSegments[0] ?? '');
  const pageName = routeNames[currentRoute] ?? pathSegments[0] ?? 'Dashboard';

  return (
    <header className="h-16 border-b border-border bg-surface/80 backdrop-blur-sm flex items-center justify-between px-6">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm">
        <span className="text-text-muted">TitoliEngine</span>
        <ChevronRight size={14} className="text-text-dim" />
        <span className="text-text font-medium">{pageName}</span>
        {pathSegments.length > 1 && (
          <>
            <ChevronRight size={14} className="text-text-dim" />
            <span className="text-text-muted">{pathSegments.slice(1).join(' / ')}</span>
          </>
        )}
      </nav>

      {/* Actions */}
      <div className="flex items-center gap-3">
        <button className="relative p-2 rounded-lg text-text-muted hover:text-text hover:bg-surface-hover transition-colors">
          <Bell size={18} />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-primary rounded-full" />
        </button>
        <button
          onClick={logout}
          className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-text-muted hover:text-text hover:bg-surface-hover transition-colors"
        >
          <LogOut size={16} />
          <span>Esci</span>
        </button>
      </div>
    </header>
  );
}
