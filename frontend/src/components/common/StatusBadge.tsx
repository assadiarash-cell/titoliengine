import { statusLabel } from '../../utils/formatters';

interface StatusBadgeProps {
  status: string;
}

const statusStyles: Record<string, { bg: string; color: string }> = {
  draft: { bg: 'var(--bg-elevated)', color: 'var(--text-secondary)' },
  generated: { bg: 'var(--color-warning)', color: 'white' },
  pending: { bg: 'var(--color-warning)', color: 'white' },
  approved: { bg: 'var(--color-success)', color: 'white' },
  posted: { bg: 'var(--color-primary)', color: 'white' },
  rejected: { bg: 'var(--color-danger)', color: 'white' },
  processed: { bg: 'var(--color-success)', color: 'white' },
  review: { bg: 'var(--color-warning)', color: 'white' },
};

export default function StatusBadge({ status }: StatusBadgeProps) {
  const style = statusStyles[status] ?? statusStyles.draft;

  return (
    <span
      className="inline-flex items-center"
      style={{
        backgroundColor: style.bg,
        color: style.color,
        fontSize: '11px',
        fontWeight: 600,
        padding: '4px 10px',
        borderRadius: '8px',
      }}
    >
      {statusLabel(status)}
    </span>
  );
}
