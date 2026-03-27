import { Briefcase, Wallet, ClipboardCheck, AlertTriangle } from 'lucide-react';
import { formatMoney } from '../../utils/formatters';
import type { QuickStatsData } from '../../types';

interface QuickStatsProps {
  data: QuickStatsData;
}

const cards = [
  { key: 'securities_count' as const, label: 'Titoli in Portafoglio', icon: Briefcase, format: (v: number) => String(v) },
  { key: 'portfolio_value' as const, label: 'Valore Totale', icon: Wallet, format: (v: string) => `€ ${formatMoney(v)}` },
  { key: 'pending_approvals' as const, label: 'Da Approvare', icon: ClipboardCheck, format: (v: number) => String(v), highlight: true },
  { key: 'parsing_discrepancies' as const, label: 'Discrepanze Parsing', icon: AlertTriangle, format: (v: number) => String(v), danger: true },
];

export default function QuickStats({ data }: QuickStatsProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map(({ key, label, icon: Icon, format, highlight, danger }) => {
        const rawValue = data[key];
        const numValue = typeof rawValue === 'number' ? rawValue : parseFloat(rawValue);
        const showAlert = (highlight || danger) && numValue > 0;

        return (
          <div
            key={key}
            className={`bg-surface border rounded-xl p-5 card-hover ${
              showAlert && danger ? 'border-danger/30' : showAlert ? 'border-primary/30 pulse-glow' : 'border-border'
            }`}
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-text-muted text-sm">{label}</span>
              <div className={`p-2 rounded-lg ${
                showAlert && danger ? 'bg-danger-dim text-danger' : showAlert ? 'bg-primary-dim text-primary' : 'bg-surface-hover text-text-muted'
              }`}>
                <Icon size={18} />
              </div>
            </div>
            <span className={`text-2xl font-money font-semibold ${
              showAlert && danger ? 'text-danger' : 'text-text'
            }`}>
              {format(rawValue as never)}
            </span>
          </div>
        );
      })}
    </div>
  );
}
