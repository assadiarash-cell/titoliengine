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
    if (action.startsWith('create')) return 'text-success';
    if (action.startsWith('update')) return 'text-accent';
    if (action.startsWith('delete')) return 'text-danger';
    return 'text-text-muted';
  };

  const columns: Column<AuditLogEntry>[] = [
    { key: 'created_at', header: 'Timestamp', render: (l) => <span className="font-money text-xs">{formatDateTime(l.created_at)}</span>, width: '160px' },
    { key: 'action', header: 'Azione', render: (l) => <span className={`text-sm font-medium ${actionColor(l.action)}`}>{l.action}</span>, width: '130px' },
    { key: 'entity_type', header: 'Entità', width: '120px' },
    { key: 'entity_id', header: 'ID', render: (l) => <span className="font-money text-xs">{l.entity_id.slice(0, 8)}...</span>, width: '100px' },
    { key: 'changes', header: 'Dettagli', render: (l) => (
      <span className="text-xs text-text-muted truncate block max-w-[300px]">
        {l.changes ? JSON.stringify(l.changes).slice(0, 80) : '—'}
      </span>
    )},
    { key: 'ip_address', header: 'IP', width: '120px', render: (l) => <span className="font-money text-xs">{l.ip_address ?? '—'}</span> },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Shield size={24} className="text-primary" />
        <div>
          <h1 className="text-3xl mb-1">Audit Log</h1>
          <p className="text-text-muted text-sm">Registro completo di tutte le operazioni</p>
        </div>
      </div>

      <div className="flex gap-3">
        <select
          value={entityFilter}
          onChange={(e) => setEntityFilter(e.target.value)}
          className="px-4 py-2.5 bg-surface border border-border rounded-lg text-sm text-text focus:outline-none focus:border-primary/50"
        >
          <option value="">Tutte le entità</option>
          <option value="security">Titoli</option>
          <option value="transaction">Operazioni</option>
          <option value="journal_entry">Scritture</option>
          <option value="document">Documenti</option>
          <option value="client">Clienti</option>
        </select>
        <select
          value={actionFilter}
          onChange={(e) => setActionFilter(e.target.value)}
          className="px-4 py-2.5 bg-surface border border-border rounded-lg text-sm text-text focus:outline-none focus:border-primary/50"
        >
          <option value="">Tutte le azioni</option>
          <option value="create">Creazione</option>
          <option value="update">Modifica</option>
          <option value="delete">Eliminazione</option>
          <option value="approve">Approvazione</option>
          <option value="post">Registrazione</option>
        </select>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-text-muted">Caricamento...</div>
      ) : (
        <DataTable columns={columns} data={logs} keyExtractor={(l) => String(l.id)} />
      )}
    </div>
  );
}
