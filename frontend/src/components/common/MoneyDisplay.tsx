import { formatMoney } from '../../utils/formatters';

interface MoneyDisplayProps {
  value: string | number;
  decimals?: number;
  currency?: string;
  className?: string;
}

/**
 * Componente per visualizzare importi monetari.
 * Font IBM Plex Mono, allineamento a destra, rosso se negativo.
 * Formato italiano: separatore migliaia punto, decimali virgola.
 */
export default function MoneyDisplay({ value, decimals = 2, currency = 'EUR', className = '' }: MoneyDisplayProps) {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  const isNegative = !isNaN(num) && num < 0;
  const formatted = formatMoney(value, decimals);

  return (
    <span
      className={`font-money text-right inline-block ${isNegative ? 'text-danger' : 'text-text'} ${className}`}
    >
      {currency === 'EUR' ? '€ ' : `${currency} `}
      {formatted}
    </span>
  );
}
