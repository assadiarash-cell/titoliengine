import { useNavigate } from 'react-router-dom';
import { CheckCircle, Clock } from 'lucide-react';
import { formatDate, formatMoney, transactionTypeLabel } from '../../utils/formatters';
import type { JournalEntry } from '../../types';

interface PendingApprovalsProps {
  entries: JournalEntry[];
}

export default function PendingApprovals({ entries }: PendingApprovalsProps) {
  const navigate = useNavigate();

  if (entries.length === 0) {
    return (
      <div className="bg-surface border border-border rounded-xl p-6">
        <h3 className="text-lg mb-4">Scritture da Approvare</h3>
        <div className="flex flex-col items-center py-8 text-text-muted">
          <CheckCircle size={32} className="mb-2 text-success" />
          <span>Nessuna scrittura in attesa</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-surface border border-border rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg">Scritture da Approvare</h3>
        <span className="text-xs text-text-muted bg-primary-dim text-primary px-2 py-1 rounded-full font-medium">
          {entries.length}
        </span>
      </div>
      <div className="space-y-2">
        {entries.slice(0, 8).map((entry) => {
          const totalDebit = entry.lines.reduce((s, l) => s + parseFloat(l.debit || '0'), 0);
          return (
            <div
              key={entry.id}
              onClick={() => navigate(`/journal/${entry.id}`)}
              className="flex items-center justify-between px-4 py-3 rounded-lg border border-border/50 cursor-pointer hover:bg-surface-hover transition-colors"
            >
              <div className="flex items-center gap-3">
                <Clock size={16} className="text-warning" />
                <div>
                  <span className="text-sm font-medium">{entry.description || transactionTypeLabel(entry.entry_type)}</span>
                  <span className="text-xs text-text-muted ml-2">{formatDate(entry.entry_date)}</span>
                </div>
              </div>
              <span className="font-money text-sm">€ {formatMoney(totalDebit)}</span>
            </div>
          );
        })}
      </div>
      {entries.length > 8 && (
        <button
          onClick={() => navigate('/journal?status=generated')}
          className="mt-3 text-sm text-primary hover:text-primary-hover transition-colors"
        >
          Vedi tutte ({entries.length})
        </button>
      )}
    </div>
  );
}
