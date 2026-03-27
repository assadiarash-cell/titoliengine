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
  if (alerts.length === 0) {
    return (
      <div className="bg-surface border border-border rounded-xl p-6">
        <h3 className="text-lg mb-4">Avvisi</h3>
        <p className="text-text-muted text-sm text-center py-6">Nessun avviso attivo</p>
      </div>
    );
  }

  return (
    <div className="bg-surface border border-border rounded-xl p-6">
      <h3 className="text-lg mb-4">Avvisi</h3>
      <div className="space-y-2">
        {alerts.map((alert) => {
          const Icon = iconMap[alert.type];
          const isCritical = alert.severity === 'critical';
          return (
            <div
              key={alert.id}
              className={`flex items-start gap-3 px-4 py-3 rounded-lg border ${
                isCritical ? 'border-danger/30 bg-danger-dim' : 'border-warning/30 bg-warning-dim'
              }`}
            >
              <Icon size={18} className={`mt-0.5 flex-shrink-0 ${isCritical ? 'text-danger' : 'text-warning'}`} />
              <div>
                <p className={`text-sm ${isCritical ? 'text-danger' : 'text-warning'}`}>{alert.message}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
