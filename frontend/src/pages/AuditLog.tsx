import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Shield } from 'lucide-react';
import api from '../api/client';
import DataTable, { type Column } from '../components/common/DataTable';
import { formatDateTime } from '../utils/formatters';
import type { AuditLogEntry } from '../types';

export default function AuditLog() {
  const [entityFilter, setEntityFilter] = useState('');
  const [actionFilter, setActionFilter] = useState('');
  const [_hoveredRow, _setHoveredRow] = useState<string | null>(null);

  const { data: logs = [], isLoading } = useQuery<AuditLogEntry[]>({
    queryKey: ['audit-log', entityFilter, actionFilter],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (entityFilter) params.entity_type = entityFilter;
      if (actionFilter) params.action = actionFilter;
      const { data } = await api.get('/audit/', { params });
      return Array.isArray(data) ? data : data.items ?? [];
    },
  });

  const actionColor = (action: string) => {
    if (action.startsWith('create')) return 'var(--color-success)';
    if (action.startsWith('update')) return 'var(--color-primary)';
    if (action.startsWith('delete')) return 'var(--color-danger)';
    return 'var(--text-secondary)';
  };

  const columns: Column<AuditLogEntry>[] = [
    {
      key: 'created_at',
      header: 'Timestamp',
      render: (l) => (
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-secondary)' }}>
          {formatDateTime(l.created_at)}
        </span>
      ),
      width: '160px',
    },
    {
      key: 'action',
      header: 'Azione',
      render: (l) => (
        <span style={{ fontSize: 14, fontWeight: 600, color: actionColor(l.action) }}>
          {l.action}
        </span>
      ),
      width: '130px',
    },
    { key: 'entity_type', header: 'Entità', width: '120px' },
    {
      key: 'entity_id',
      header: 'ID',
      render: (l) => (
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-secondary)' }}>
          {l.entity_id.slice(0, 8)}...
        </span>
      ),
      width: '100px',
    },
    {
      key: 'changes',
      header: 'Dettagli',
      render: (l) => (
        <span
          style={{
            fontSize: 12,
            color: 'var(--text-secondary)',
            display: 'block',
            maxWidth: 300,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {l.changes ? JSON.stringify(l.changes).slice(0, 80) : '\u2014'}
        </span>
      ),
    },
    {
      key: 'ip_address',
      header: 'IP',
      width: '120px',
      render: (l) => (
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-secondary)' }}>
          {l.ip_address ?? '\u2014'}
        </span>
      ),
    },
  ];

  const selectStyle: React.CSSProperties = {
    padding: '10px 18px',
    backgroundColor: 'var(--bg-primary)',
    color: 'var(--text-primary)',
    border: 'none',
    borderRadius: 16,
    fontSize: 14,
    boxShadow: 'var(--shadow-neumorphic-in)',
    outline: 'none',
    cursor: 'pointer',
    appearance: 'none' as const,
    WebkitAppearance: 'none' as const,
    backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2398989D' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E")`,
    backgroundRepeat: 'no-repeat',
    backgroundPosition: 'right 14px center',
    paddingRight: 36,
  };

  return (
    <div style={{ padding: 32, backgroundColor: 'var(--bg-primary)', minHeight: '100vh' }}>
      {/* Breadcrumb + Header */}
      <p style={{ fontSize: 13, color: 'var(--text-secondary)', fontWeight: 500, marginBottom: 4 }}>
        Dashboard / Audit Log
      </p>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <div
          style={{
            width: 40,
            height: 40,
            borderRadius: 12,
            backgroundColor: 'var(--bg-surface)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: 'var(--shadow-neumorphic-out)',
          }}
        >
          <Shield size={20} style={{ color: 'var(--color-primary)' }} />
        </div>
        <h1 style={{ fontSize: 32, fontWeight: 600, letterSpacing: '-0.02em', color: 'var(--text-primary)', margin: 0 }}>
          Audit Log
        </h1>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 24 }}>
        <select value={entityFilter} onChange={(e) => setEntityFilter(e.target.value)} style={selectStyle}>
          <option value="">Tutte le entità</option>
          <option value="security">Titoli</option>
          <option value="transaction">Operazioni</option>
          <option value="journal_entry">Scritture</option>
          <option value="document">Documenti</option>
          <option value="client">Clienti</option>
        </select>
        <select value={actionFilter} onChange={(e) => setActionFilter(e.target.value)} style={selectStyle}>
          <option value="">Tutte le azioni</option>
          <option value="create">Creazione</option>
          <option value="update">Modifica</option>
          <option value="delete">Eliminazione</option>
          <option value="approve">Approvazione</option>
          <option value="post">Registrazione</option>
        </select>
      </div>

      {/* Table */}
      {isLoading ? (
        <div style={{ textAlign: 'center', padding: '48px 0', color: 'var(--text-secondary)' }}>Caricamento...</div>
      ) : (
        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            borderRadius: 24,
            boxShadow: 'var(--shadow-neumorphic-out)',
            overflow: 'hidden',
          }}
        >
          <DataTable columns={columns} data={logs} keyExtractor={(l) => String(l.id)} />
        </div>
      )}
    </div>
  );
}
