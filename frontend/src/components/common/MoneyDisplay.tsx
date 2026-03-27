import { formatMoney } from '../../utils/formatters';

interface MoneyDisplayProps {
  value: string | number;
  decimals?: number;
  currency?: string;
  className?: string;
}

export default function MoneyDisplay({ value, decimals = 2, currency = 'EUR', className = '' }: MoneyDisplayProps) {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  const isNegative = !isNaN(num) && num < 0;
  const formatted = formatMoney(value, decimals);

  return (
    <span
      className={`font-money text-right inline-block ${className}`}
      style={{
        fontFamily: 'var(--font-mono)',
        color: isNegative ? 'var(--color-danger)' : 'var(--text-primary)',
        fontWeight: 600,
      }}
    >
      {currency === 'EUR' ? '€ ' : `${currency} `}
      {formatted}
    </span>
  );
}
