import { AlertTriangle, TrendingDown, FileWarning } from 'lucide-react';

export interface Alert {
  id: string;
  type: 'low_confidence' | 'valuation_expired' | 'balance_mismatch';
  message: string;
  severity: 'warning' | 'critical';
  timestamp: string;
}

interface AlertsPanelProps {
  alerts: Alert[];
}

const iconMap = {
  low_confidence: FileWarning,
  valuation_expired: TrendingDown,
  balance_mismatch: AlertTriangle,
};

export default function AlertsPanel({ alerts }: AlertsPanelProps) {
  return (
    <div
      className="rounded-3xl"
      style={{
        background: 'var(--bg-surface)',
        boxShadow: 'var(--shadow-neumorphic-out)',
      }}
    >
      <div className="p-6" style={{ borderBottom: '1px solid var(--border-default)' }}>
        <h2 style={{ fontSize: '20px', fontWeight: 600, color: 'var(--text-primary)', letterSpacing: '-0.01em' }}>
          Attività Recente
        </h2>
      </div>
      <div className="p-6">
        {alerts.length === 0 ? (
          <p style={{ color: 'var(--text-secondary)', fontSize: '15px', fontWeight: 500, textAlign: 'center', padding: '24px 0' }}>
            Nessun avviso attivo
          </p>
        ) : (
          <div className="space-y-6">
            {alerts.map((alert, idx) => {
              const Icon = iconMap[alert.type];
              const dotColor = alert.severity === 'critical' ? 'var(--color-danger)' : 'var(--color-warning)';
              return (
                <div key={alert.id} className="flex gap-4">
                  <div className="relative">
                    <div
                      className="w-2.5 h-2.5 rounded-full mt-2"
                      style={{ backgroundColor: dotColor }}
                    />
                    {idx < alerts.length - 1 && (
                      <div className="absolute left-1 top-5 w-px h-8" style={{ backgroundColor: 'var(--border-default)' }} />
                    )}
                  </div>
                  <div className="flex-1">
                    <div style={{ fontSize: '15px', color: 'var(--text-primary)', marginBottom: '4px', fontWeight: 500 }}>
                      {alert.message}
                    </div>
                    <div style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: 500 }}>
                      {alert.timestamp}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
