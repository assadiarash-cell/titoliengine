import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { BookOpen, Play, Check, Send } from 'lucide-react';
import api from '../api/client';
import DataTable, { type Column } from '../components/common/DataTable';
import MoneyDisplay from '../components/common/MoneyDisplay';
import StatusBadge from '../components/common/StatusBadge';
import { formatDate } from '../utils/formatters';
import type { JournalEntry, BalanceCheck } from '../types';

export default function Journal() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [selectedEntry, setSelectedEntry] = useState<JournalEntry | null>(null);

  const { data: entries = [], isLoading } = useQuery<JournalEntry[]>({
    queryKey: ['journal-entries', statusFilter],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (statusFilter) params.status = statusFilter;
      const { data } = await api.get('/journal/entries', { params });
      return Array.isArray(data) ? data : data.items ?? [];
    },
  });

  const { data: balanceCheck } = useQuery<BalanceCheck>({
    queryKey: ['balance-check'],
    queryFn: async () => {
      const { data } = await api.get('/journal/balance-check');
      return data;
    },
  });

  const generateMutation = useMutation({
    mutationFn: () => api.post('/journal/generate'),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['journal-entries'] }),
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) => api.post(`/journal/${id}/approve`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['journal-entries'] }),
  });

  const postMutation = useMutation({
    mutationFn: (id: string) => api.post(`/journal/${id}/post`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['journal-entries'] }),
  });

  const columns: Column<JournalEntry>[] = [
    { key: 'entry_date', header: 'Data', render: (e) => formatDate(e.entry_date), width: '100px' },
    { key: 'reference', header: 'Riferimento', width: '150px' },
    { key: 'entry_type', header: 'Tipo', width: '100px' },
    { key: 'description', header: 'Descrizione' },
    {
      key: 'total',
      header: 'Importo',
      align: 'right',
      render: (e) => {
        const total = e.lines.reduce((s, l) => s + parseFloat(l.debit || '0'), 0);
        return <MoneyDisplay value={total} />;
      },
    },
    { key: 'status', header: 'Stato', render: (e) => <StatusBadge status={e.status} />, width: '110px' },
    {
      key: 'actions',
      header: '',
      sortable: false,
      width: '80px',
      render: (e) => (
        <div className="flex gap-1">
          {e.status === 'generated' && (
            <button onClick={(ev) => { ev.stopPropagation(); approveMutation.mutate(e.id); }}
              className="p-1 text-text-dim hover:text-accent" title="Approva"><Check size={14} /></button>
          )}
          {e.status === 'approved' && (
            <button onClick={(ev) => { ev.stopPropagation(); postMutation.mutate(e.id); }}
              className="p-1 text-text-dim hover:text-success" title="Registra"><Send size={14} /></button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl mb-1">Scritture Contabili</h1>
          <p className="text-text-muted text-sm">Partita doppia — OIC 20</p>
        </div>
        <button
          onClick={() => generateMutation.mutate()}
          disabled={generateMutation.isPending}
          className="flex items-center gap-2 px-4 py-2.5 bg-primary text-background rounded-lg text-sm font-medium hover:bg-primary-hover disabled:opacity-50 transition-colors"
        >
          <Play size={16} />
          {generateMutation.isPending ? 'Generazione...' : 'Genera Scritture'}
        </button>
      </div>

      {/* Balance check banner */}
      {balanceCheck && (
        <div className={`flex items-center gap-3 px-4 py-3 rounded-lg border ${
          balanceCheck.is_balanced ? 'border-success/30 bg-success-dim' : 'border-danger/30 bg-danger-dim'
        }`}>
          <BookOpen size={18} className={balanceCheck.is_balanced ? 'text-success' : 'text-danger'} />
          <span className={`text-sm ${balanceCheck.is_balanced ? 'text-success' : 'text-danger'}`}>
            {balanceCheck.is_balanced
              ? `Quadratura OK — ${balanceCheck.entries_count} scritture, dare = avere`
              : `SQUILIBRIO — Differenza: € ${balanceCheck.difference}`
            }
          </span>
          <span className="ml-auto font-money text-sm text-text-muted">
            D: € {parseFloat(balanceCheck.total_debit).toLocaleString('it-IT', { minimumFractionDigits: 2 })}
            {' | '}
            A: € {parseFloat(balanceCheck.total_credit).toLocaleString('it-IT', { minimumFractionDigits: 2 })}
          </span>
        </div>
      )}

      <div className="flex gap-3">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2.5 bg-surface border border-border rounded-lg text-sm text-text focus:outline-none focus:border-primary/50"
        >
          <option value="">Tutti gli stati</option>
          <option value="generated">Generata</option>
          <option value="approved">Approvata</option>
          <option value="posted">Registrata</option>
        </select>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-text-muted">Caricamento...</div>
      ) : (
        <DataTable
          columns={columns}
          data={entries}
          keyExtractor={(e) => e.id}
          onRowClick={(e) => setSelectedEntry(e)}
        />
      )}

      {/* Entry detail modal */}
      {selectedEntry && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-6" onClick={() => setSelectedEntry(null)}>
          <div className="bg-surface border border-border rounded-xl p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg">{selectedEntry.description || selectedEntry.reference}</h3>
              <StatusBadge status={selectedEntry.status} />
            </div>
            <p className="text-sm text-text-muted mb-4">Data: {formatDate(selectedEntry.entry_date)} — Tipo: {selectedEntry.entry_type}</p>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-text-muted">
                  <th className="text-left py-2">Conto</th>
                  <th className="text-left py-2">Descrizione</th>
                  <th className="text-right py-2">Dare</th>
                  <th className="text-right py-2">Avere</th>
                </tr>
              </thead>
              <tbody>
                {selectedEntry.lines.map((line) => (
                  <tr key={line.id} className="border-b border-border/50">
                    <td className="py-2 font-money text-xs">{line.account_code}</td>
                    <td className="py-2">{line.account_name}</td>
                    <td className="py-2 text-right">{parseFloat(line.debit) > 0 ? <MoneyDisplay value={line.debit} /> : ''}</td>
                    <td className="py-2 text-right">{parseFloat(line.credit) > 0 ? <MoneyDisplay value={line.credit} /> : ''}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="font-medium border-t border-border">
                  <td colSpan={2} className="py-2">Totale</td>
                  <td className="py-2 text-right">
                    <MoneyDisplay value={selectedEntry.lines.reduce((s, l) => s + parseFloat(l.debit || '0'), 0)} />
                  </td>
                  <td className="py-2 text-right">
                    <MoneyDisplay value={selectedEntry.lines.reduce((s, l) => s + parseFloat(l.credit || '0'), 0)} />
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
