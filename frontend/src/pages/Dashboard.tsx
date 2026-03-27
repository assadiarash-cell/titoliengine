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
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl mb-1">Dashboard</h1>
        <p className="text-text-muted text-sm">Panoramica del portafoglio titoli e attività in sospeso</p>
      </div>

      <QuickStats data={stats ?? defaultStats} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PendingApprovals entries={pendingEntries ?? []} />
        <AlertsPanel alerts={alerts ?? []} />
      </div>
    </div>
  );
}
