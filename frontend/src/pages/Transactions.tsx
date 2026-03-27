import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Search, Check, RotateCcw } from 'lucide-react';
import api from '../api/client';
import DataTable, { type Column } from '../components/common/DataTable';
import MoneyDisplay from '../components/common/MoneyDisplay';
import StatusBadge from '../components/common/StatusBadge';
import { formatDate, transactionTypeLabel } from '../utils/formatters';
import type { Transaction } from '../types';

export default function Transactions() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');

  const { data: transactions = [], isLoading } = useQuery<Transaction[]>({
    queryKey: ['transactions', statusFilter],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (statusFilter) params.status = statusFilter;
      const { data } = await api.get('/transactions/', { params });
      return Array.isArray(data) ? data : data.items ?? [];
    },
  });

  const filtered = transactions.filter(
    (t) =>
      t.transaction_type.toLowerCase().includes(search.toLowerCase()) ||
      t.notes?.toLowerCase().includes(search.toLowerCase()) ||
      t.id.includes(search)
  );

  const approveMutation = useMutation({
    mutationFn: (id: string) => api.post(`/transactions/${id}/approve`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['transactions'] }),
  });

  const rejectMutation = useMutation({
    mutationFn: (id: string) => api.post(`/transactions/${id}/reject`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['transactions'] }),
  });

  const columns: Column<Transaction>[] = [
    { key: 'trade_date', header: 'Data Op.', render: (t) => formatDate(t.trade_date), width: '100px' },
    { key: 'transaction_type', header: 'Tipo', render: (t) => transactionTypeLabel(t.transaction_type), width: '100px' },
    { key: 'quantity', header: 'Quantità', align: 'right', render: (t) => <span className="font-money">{t.quantity}</span>, width: '100px' },
    { key: 'unit_price', header: 'Prezzo', align: 'right', render: (t) => <MoneyDisplay value={t.unit_price} />, width: '120px' },
    { key: 'total_amount', header: 'Totale', align: 'right', render: (t) => <MoneyDisplay value={t.total_amount} />, width: '140px' },
    { key: 'settlement_date', header: 'Regol.', render: (t) => formatDate(t.settlement_date), width: '100px' },
    { key: 'status', header: 'Stato', render: (t) => <StatusBadge status={t.status} />, width: '110px' },
    {
      key: 'actions',
      header: '',
      sortable: false,
      width: '80px',
      render: (t) => (
        <div className="flex gap-1">
          {t.status === 'draft' && (
            <button
              onClick={(e) => { e.stopPropagation(); approveMutation.mutate(t.id); }}
              className="p-1 text-text-dim hover:text-success" title="Approva"
            ><Check size={14} /></button>
          )}
          {t.status === 'approved' && (
            <button
              onClick={(e) => { e.stopPropagation(); rejectMutation.mutate(t.id); }}
              className="p-1 text-text-dim hover:text-warning" title="Rigetta"
            ><RotateCcw size={14} /></button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl mb-1">Operazioni</h1>
          <p className="text-text-muted text-sm">Registro operazioni su titoli</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2.5 bg-primary text-background rounded-lg text-sm font-medium hover:bg-primary-hover transition-colors">
          <Plus size={16} /> Nuova Operazione
        </button>
      </div>

      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
          <input
            type="text"
            placeholder="Cerca operazioni..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-surface border border-border rounded-lg text-sm text-text placeholder-text-dim focus:outline-none focus:border-primary/50"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2.5 bg-surface border border-border rounded-lg text-sm text-text focus:outline-none focus:border-primary/50"
        >
          <option value="">Tutti gli stati</option>
          <option value="draft">Bozza</option>
          <option value="approved">Approvata</option>
          <option value="posted">Registrata</option>
        </select>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-text-muted">Caricamento...</div>
      ) : (
        <DataTable columns={columns} data={filtered} keyExtractor={(t) => t.id} />
      )}
    </div>
  );
}
