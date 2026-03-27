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
        <div style={{ display: 'flex', gap: '4px' }}>
          {e.status === 'generated' && (
            <button
              onClick={(ev) => { ev.stopPropagation(); approveMutation.mutate(e.id); }}
              style={{
                padding: '6px',
                borderRadius: '10px',
                border: 'none',
                background: 'transparent',
                color: 'var(--text-tertiary)',
                cursor: 'pointer',
                transition: 'color 0.2s, background 0.2s',
              }}
              onMouseEnter={(ev) => {
                ev.currentTarget.style.color = 'var(--color-primary)';
                ev.currentTarget.style.background = 'var(--bg-elevated)';
              }}
              onMouseLeave={(ev) => {
                ev.currentTarget.style.color = 'var(--text-tertiary)';
                ev.currentTarget.style.background = 'transparent';
              }}
              title="Approva"
            >
              <Check size={14} />
            </button>
          )}
          {e.status === 'approved' && (
            <button
              onClick={(ev) => { ev.stopPropagation(); postMutation.mutate(e.id); }}
              style={{
                padding: '6px',
                borderRadius: '10px',
                border: 'none',
                background: 'transparent',
                color: 'var(--text-tertiary)',
                cursor: 'pointer',
                transition: 'color 0.2s, background 0.2s',
              }}
              onMouseEnter={(ev) => {
                ev.currentTarget.style.color = 'var(--color-success)';
                ev.currentTarget.style.background = 'var(--bg-elevated)';
              }}
              onMouseLeave={(ev) => {
                ev.currentTarget.style.color = 'var(--text-tertiary)';
                ev.currentTarget.style.background = 'transparent';
              }}
              title="Registra"
            >
              <Send size={14} />
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
          Dashboard / Scritture Contabili
        </p>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <h1 style={{ fontSize: '32px', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
            Scritture Contabili
          </h1>
          <button
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '12px 24px',
              background: generateMutation.isPending ? 'var(--bg-elevated)' : 'var(--color-primary)',
              color: '#FFFFFF',
              border: 'none',
              borderRadius: '16px',
              fontSize: '14px',
              fontWeight: 600,
              cursor: generateMutation.isPending ? 'not-allowed' : 'pointer',
              boxShadow: generateMutation.isPending ? 'none' : '0 0 20px rgba(10, 132, 255, 0.3)',
              opacity: generateMutation.isPending ? 0.5 : 1,
              transition: 'box-shadow 0.2s, background 0.2s, opacity 0.2s',
            }}
            onMouseEnter={(e) => {
              if (!generateMutation.isPending) {
                e.currentTarget.style.background = 'var(--color-primary-hover)';
                e.currentTarget.style.boxShadow = '0 0 28px rgba(10, 132, 255, 0.45)';
              }
            }}
            onMouseLeave={(e) => {
              if (!generateMutation.isPending) {
                e.currentTarget.style.background = 'var(--color-primary)';
                e.currentTarget.style.boxShadow = '0 0 20px rgba(10, 132, 255, 0.3)';
              }
            }}
          >
            <Play size={16} />
            {generateMutation.isPending ? 'Generazione...' : 'Genera Scritture'}
          </button>
        </div>
      </div>

      {/* Balance check banner */}
      {balanceCheck && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '16px 20px',
            borderRadius: '16px',
            background: 'var(--bg-surface)',
            boxShadow: 'var(--shadow-neumorphic-subtle)',
            marginBottom: '24px',
            borderLeft: `4px solid ${balanceCheck.is_balanced ? 'var(--color-success)' : 'var(--color-danger)'}`,
          }}
        >
          <BookOpen
            size={18}
            style={{ color: balanceCheck.is_balanced ? 'var(--color-success)' : 'var(--color-danger)' }}
          />
          <span
            style={{
              fontSize: '14px',
              fontWeight: 500,
              color: balanceCheck.is_balanced ? 'var(--color-success)' : 'var(--color-danger)',
            }}
          >
            {balanceCheck.is_balanced
              ? `Quadratura OK — ${balanceCheck.entries_count} scritture, dare = avere`
              : `SQUILIBRIO — Differenza: \u20AC ${balanceCheck.difference}`}
          </span>
          <span
            style={{
              marginLeft: 'auto',
              fontFamily: 'var(--font-mono)',
              fontSize: '13px',
              color: 'var(--text-secondary)',
            }}
          >
            D: &euro; {parseFloat(balanceCheck.total_debit).toLocaleString('it-IT', { minimumFractionDigits: 2 })}
            {' | '}
            A: &euro; {parseFloat(balanceCheck.total_credit).toLocaleString('it-IT', { minimumFractionDigits: 2 })}
          </span>
        </div>
      )}

      {/* Filter */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '24px' }}>
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
          <option value="generated">Generata</option>
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
        <DataTable
          columns={columns}
          data={entries}
          keyExtractor={(e) => e.id}
          onRowClick={(e) => setSelectedEntry(e)}
        />
      )}

      {/* Entry detail modal */}
      {selectedEntry && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 50,
            padding: '24px',
            backdropFilter: 'blur(4px)',
          }}
          onClick={() => setSelectedEntry(null)}
        >
          <div
            style={{
              background: 'var(--bg-surface)',
              borderRadius: '24px',
              padding: '28px',
              maxWidth: '720px',
              width: '100%',
              maxHeight: '80vh',
              overflowY: 'auto',
              boxShadow: 'var(--shadow-elevated)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
                {selectedEntry.description || selectedEntry.reference}
              </h3>
              <StatusBadge status={selectedEntry.status} />
            </div>

            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '20px' }}>
              Data: {formatDate(selectedEntry.entry_date)} — Tipo: {selectedEntry.entry_type}
            </p>

            {/* Lines table */}
            <div
              style={{
                borderRadius: '16px',
                overflow: 'hidden',
                background: 'var(--bg-primary)',
                boxShadow: 'var(--shadow-neumorphic-in)',
              }}
            >
              <table style={{ width: '100%', fontSize: '14px', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-default)' }}>
                    <th style={{ textAlign: 'left', padding: '14px 16px', fontSize: '11px', fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                      Conto
                    </th>
                    <th style={{ textAlign: 'left', padding: '14px 16px', fontSize: '11px', fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                      Descrizione
                    </th>
                    <th style={{ textAlign: 'right', padding: '14px 16px', fontSize: '11px', fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                      Dare
                    </th>
                    <th style={{ textAlign: 'right', padding: '14px 16px', fontSize: '11px', fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                      Avere
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {selectedEntry.lines.map((line) => (
                    <tr
                      key={line.id}
                      style={{ borderBottom: '1px solid var(--border-default)' }}
                      onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'var(--bg-elevated)'; }}
                      onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; }}
                    >
                      <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-secondary)' }}>
                        {line.account_code}
                      </td>
                      <td style={{ padding: '12px 16px', color: 'var(--text-primary)' }}>
                        {line.account_name}
                      </td>
                      <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                        {parseFloat(line.debit) > 0 ? <MoneyDisplay value={line.debit} /> : ''}
                      </td>
                      <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                        {parseFloat(line.credit) > 0 ? <MoneyDisplay value={line.credit} /> : ''}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr style={{ borderTop: '2px solid var(--border-default)' }}>
                    <td colSpan={2} style={{ padding: '14px 16px', fontWeight: 600, color: 'var(--text-primary)' }}>
                      Totale
                    </td>
                    <td style={{ padding: '14px 16px', textAlign: 'right' }}>
                      <MoneyDisplay value={selectedEntry.lines.reduce((s, l) => s + parseFloat(l.debit || '0'), 0)} />
                    </td>
                    <td style={{ padding: '14px 16px', textAlign: 'right' }}>
                      <MoneyDisplay value={selectedEntry.lines.reduce((s, l) => s + parseFloat(l.credit || '0'), 0)} />
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
