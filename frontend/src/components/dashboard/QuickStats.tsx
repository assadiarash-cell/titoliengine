import { TrendingUp } from 'lucide-react';
import { formatMoney } from '../../utils/formatters';
import type { QuickStatsData } from '../../types';

interface QuickStatsProps {
  data: QuickStatsData;
}

export default function QuickStats({ data }: QuickStatsProps) {
  const cards = [
    {
      label: 'Titoli in Portafoglio',
      value: String(data.securities_count),
      large: true,
    },
    {
      label: 'Valore Contabile Totale',
      value: `€${formatMoney(data.portfolio_value)}`,
      mono: true,
      showTrend: true,
    },
    {
      label: 'Scritture da Approvare',
      value: String(data.pending_approvals),
      large: true,
      warning: data.pending_approvals > 0,
    },
    {
      label: 'Discrepanze Parsing',
      value: String(data.parsing_discrepancies),
      large: true,
    },
  ];

  return (
    <div className="grid grid-cols-4 gap-6">
      {cards.map(({ label, value, large, mono, showTrend, warning }) => (
        <div
          key={label}
          className="rounded-3xl p-6"
          style={{
            background: 'var(--bg-surface)',
            boxShadow: 'var(--shadow-neumorphic-out)',
          }}
        >
          <div
            style={{
              fontSize: '11px',
              color: 'var(--text-tertiary)',
              marginBottom: '12px',
              fontWeight: 600,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
            }}
          >
            {label}
          </div>
          <div className="flex items-center gap-3">
            <div
              style={{
                fontFamily: mono ? 'var(--font-mono)' : 'var(--font-system)',
                fontSize: large ? '40px' : '24px',
                color: 'var(--text-primary)',
                lineHeight: 1,
                fontWeight: 600,
                letterSpacing: large ? '-0.02em' : undefined,
              }}
            >
              {value}
            </div>
            {warning && (
              <span
                style={{
                  backgroundColor: 'var(--color-warning)',
                  color: 'white',
                  fontSize: '11px',
                  fontWeight: 600,
                  padding: '4px 10px',
                  borderRadius: '8px',
                }}
              >
                Attenzione
              </span>
            )}
          </div>
          {showTrend && (
            <div
              className="flex items-center gap-1 mt-2"
              style={{ color: 'var(--color-success)', fontSize: '14px', fontWeight: 600 }}
            >
              <TrendingUp className="w-4 h-4" />
              <span>+2.4%</span>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
