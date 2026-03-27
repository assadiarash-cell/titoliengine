import { useQuery } from '@tanstack/react-query';
import QuickStats from '../components/dashboard/QuickStats';
import PendingApprovals from '../components/dashboard/PendingApprovals';
import AlertsPanel, { type Alert } from '../components/dashboard/AlertsPanel';
import api from '../api/client';
import type { QuickStatsData, JournalEntry } from '../types';

export default function Dashboard() {
  const { data: stats } = useQuery<QuickStatsData>({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      try {
        const { data } = await api.get('/dashboard/stats');
        return data;
      } catch {
        return { securities_count: 0, portfolio_value: '0', pending_approvals: 0, parsing_discrepancies: 0 };
      }
    },
  });

  const { data: pendingEntries } = useQuery<JournalEntry[]>({
    queryKey: ['pending-approvals'],
    queryFn: async () => {
      try {
        const { data } = await api.get('/journal/entries', { params: { status: 'generated' } });
        return Array.isArray(data) ? data : data.items ?? [];
      } catch {
        return [];
      }
    },
  });

  const { data: alerts } = useQuery<Alert[]>({
    queryKey: ['dashboard-alerts'],
    queryFn: async () => {
      try {
        const { data } = await api.get('/dashboard/alerts');
        return data;
      } catch {
        return [];
      }
    },
  });

  const defaultStats: QuickStatsData = {
    securities_count: 0,
    portfolio_value: '0',
    pending_approvals: 0,
    parsing_discrepancies: 0,
  };

  return (
    <div
      style={{
        padding: '32px',
        backgroundColor: 'var(--bg-primary)',
        minHeight: '100%',
        fontFamily: 'var(--font-system)',
      }}
    >
      {/* Page Header */}
      <div style={{ marginBottom: '32px' }}>
        <p
          style={{
            fontSize: '13px',
            color: 'var(--text-secondary)',
            fontWeight: 500,
            marginBottom: '4px',
          }}
        >
          TitoliEngine &rsaquo; Dashboard
        </p>
        <h1
          style={{
            fontSize: '32px',
            fontWeight: 600,
            letterSpacing: '-0.02em',
            color: 'var(--text-primary)',
            margin: 0,
          }}
        >
          Dashboard
        </h1>
      </div>

      {/* Quick Stats */}
      <div style={{ marginBottom: '32px' }}>
        <QuickStats data={stats ?? defaultStats} />
      </div>

      {/* Two-column grid: PendingApprovals (60%) + AlertsPanel (40%) */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '3fr 2fr',
          gap: '24px',
        }}
      >
        <PendingApprovals entries={pendingEntries ?? []} />
        <AlertsPanel alerts={alerts ?? []} />
      </div>
    </div>
  );
}
