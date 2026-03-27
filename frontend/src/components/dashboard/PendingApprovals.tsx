import { useNavigate } from 'react-router-dom';
import { ArrowUpRight, CheckCircle, Clock } from 'lucide-react';
import { formatDate, formatMoney, transactionTypeLabel } from '../../utils/formatters';
import type { JournalEntry } from '../../types';

interface PendingApprovalsProps {
  entries: JournalEntry[];
}

export default function PendingApprovals({ entries }: PendingApprovalsProps) {
  const navigate = useNavigate();

  return (
    <div
      className="rounded-3xl overflow-hidden"
      style={{
        background: 'var(--bg-surface)',
        boxShadow: 'var(--shadow-neumorphic-out)',
      }}
    >
      <div className="p-6" style={{ borderBottom: '1px solid var(--border-default)' }}>
        <h2 style={{ fontSize: '20px', fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.01em' }}>
          Scritture in Attesa
        </h2>
      </div>

      {entries.length === 0 ? (
        <div className="flex flex-col items-center py-12" style={{ color: 'var(--text-secondary)' }}>
          <CheckCircle size={32} className="mb-2" style={{ color: 'var(--color-success)' }} />
          <span style={{ fontSize: '15px', fontWeight: 500 }}>Nessuna scrittura in attesa</span>
        </div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-default)' }}>
                  {['Data', 'Tipo', 'Descrizione', 'Importo', 'Status'].map((h) => (
                    <th
                      key={h}
                      className={`p-4 ${h === 'Importo' ? 'text-right' : 'text-left'}`}
                      style={{
                        fontSize: '11px',
                        fontWeight: 600,
                        color: 'var(--text-tertiary)',
                        textTransform: 'uppercase',
                        letterSpacing: '0.08em',
                      }}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {entries.slice(0, 8).map((entry) => {
                  const totalDebit = entry.lines.reduce((s, l) => s + parseFloat(l.debit || '0'), 0);
                  return (
                    <tr
                      key={entry.id}
                      className="cursor-pointer transition-all duration-200"
                      style={{ borderBottom: '1px solid var(--border-default)' }}
                      onClick={() => navigate('/journal')}
                      onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'var(--bg-elevated)'; }}
                      onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; }}
                    >
                      <td className="p-4" style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', color: 'var(--text-primary)', fontWeight: 500 }}>
                        {formatDate(entry.entry_date)}
                      </td>
                      <td className="p-4" style={{ fontSize: '15px', color: 'var(--text-primary)', fontWeight: 500 }}>
                        {transactionTypeLabel(entry.entry_type)}
                      </td>
                      <td className="p-4" style={{ fontSize: '15px', color: 'var(--text-secondary)', fontWeight: 500 }}>
                        {entry.description || entry.reference}
                      </td>
                      <td className="p-4 text-right" style={{ fontFamily: 'var(--font-mono)', fontSize: '15px', color: 'var(--text-primary)', fontWeight: 600 }}>
                        €{formatMoney(totalDebit)}
                      </td>
                      <td className="p-4">
                        <span style={{
                          backgroundColor: 'var(--color-warning)',
                          color: 'white',
                          fontSize: '11px',
                          fontWeight: 600,
                          padding: '4px 10px',
                          borderRadius: '8px',
                        }}>
                          Da approvare
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {entries.length > 8 && (
            <div className="p-4" style={{ borderTop: '1px solid var(--border-default)' }}>
              <button
                onClick={() => navigate('/journal?status=generated')}
                className="flex items-center gap-2 px-4 py-2 rounded-xl transition-all duration-200"
                style={{ color: 'var(--color-primary)', fontSize: '15px', fontWeight: 600 }}
                onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--bg-elevated)'; }}
                onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
              >
                Vedi tutte ({entries.length}) <ArrowUpRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
