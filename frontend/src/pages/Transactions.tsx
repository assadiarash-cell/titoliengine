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
        <div style={{ display: 'flex', gap: '4px' }}>
          {t.status === 'draft' && (
            <button
              onClick={(e) => { e.stopPropagation(); approveMutation.mutate(t.id); }}
              style={{
                padding: '6px',
                borderRadius: '10px',
                border: 'none',
                background: 'transparent',
                color: 'var(--text-tertiary)',
                cursor: 'pointer',
                transition: 'color 0.2s, background 0.2s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = 'var(--color-success)';
                e.currentTarget.style.background = 'var(--bg-elevated)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = 'var(--text-tertiary)';
                e.currentTarget.style.background = 'transparent';
              }}
              title="Approva"
            >
              <Check size={14} />
            </button>
          )}
          {t.status === 'approved' && (
            <button
              onClick={(e) => { e.stopPropagation(); rejectMutation.mutate(t.id); }}
              style={{
                padding: '6px',
                borderRadius: '10px',
                border: 'none',
                background: 'transparent',
                color: 'var(--text-tertiary)',
                cursor: 'pointer',
                transition: 'color 0.2s, background 0.2s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = 'var(--color-warning)';
                e.currentTarget.style.background = 'var(--bg-elevated)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = 'var(--text-tertiary)';
                e.currentTarget.style.background = 'transparent';
              }}
              title="Rigetta"
            >
              <RotateCcw size={14} />
            </button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div style={{ padding: '32px', background: 'var(--bg-primary)', minHeight: '100%' }}>
      {/* Breadcrumb + Header */}
      <div style={{ marginBottom: '32px' }}>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
          Dashboard / Operazioni
        </p>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <h1 style={{ fontSize: '32px', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
            Operazioni
          </h1>
          <button
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '12px 24px',
              background: 'var(--color-primary)',
              color: '#FFFFFF',
              border: 'none',
              borderRadius: '16px',
              fontSize: '14px',
              fontWeight: 600,
              cursor: 'pointer',
              boxShadow: '0 0 20px rgba(10, 132, 255, 0.3)',
              transition: 'box-shadow 0.2s, background 0.2s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'var(--color-primary-hover)';
              e.currentTarget.style.boxShadow = '0 0 28px rgba(10, 132, 255, 0.45)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'var(--color-primary)';
              e.currentTarget.style.boxShadow = '0 0 20px rgba(10, 132, 255, 0.3)';
            }}
          >
            <Plus size={16} /> Nuova Operazione
          </button>
        </div>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '24px' }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <Search
            size={16}
            style={{
              position: 'absolute',
              left: '16px',
              top: '50%',
              transform: 'translateY(-50%)',
              color: 'var(--text-tertiary)',
              pointerEvents: 'none',
            }}
          />
          <input
            type="text"
            placeholder="Cerca operazioni..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              width: '100%',
              paddingLeft: '44px',
              paddingRight: '16px',
              paddingTop: '12px',
              paddingBottom: '12px',
              background: 'var(--bg-surface)',
              border: 'none',
              borderRadius: '16px',
              fontSize: '14px',
              color: 'var(--text-primary)',
              boxShadow: 'var(--shadow-neumorphic-in)',
              outline: 'none',
              boxSizing: 'border-box',
            }}
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          style={{
            padding: '12px 20px',
            background: 'var(--bg-surface)',
            border: 'none',
            borderRadius: '16px',
            fontSize: '14px',
            color: 'var(--text-primary)',
            boxShadow: 'var(--shadow-neumorphic-in)',
            outline: 'none',
            cursor: 'pointer',
            appearance: 'auto' as React.CSSProperties['appearance'],
          }}
        >
          <option value="">Tutti gli stati</option>
          <option value="draft">Bozza</option>
          <option value="approved">Approvata</option>
          <option value="posted">Registrata</option>
        </select>
      </div>

      {/* Table */}
      {isLoading ? (
        <div style={{ textAlign: 'center', padding: '48px 0', color: 'var(--text-secondary)' }}>
          Caricamento...
        </div>
      ) : (
        <DataTable columns={columns} data={filtered} keyExtractor={(t) => t.id} />
      )}
    </div>
  );
}
