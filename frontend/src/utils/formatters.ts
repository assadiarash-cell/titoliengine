/**
 * Formatta un importo numerico in formato italiano: 1.234,56
 * Separatore migliaia: punto. Separatore decimali: virgola.
 */
export function formatMoney(value: string | number, decimals = 2): string {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return '—';
  return num.toLocaleString('it-IT', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

/**
 * Formatta una data ISO in formato italiano: dd/mm/yyyy
 */
export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleDateString('it-IT', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

/**
 * Formatta una data ISO con orario
 */
export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleDateString('it-IT', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Mappa tipo operazione a label italiano
 */
export function transactionTypeLabel(type: string): string {
  const map: Record<string, string> = {
    purchase: 'Acquisto',
    sale: 'Vendita',
    coupon: 'Cedola',
    maturity: 'Rimborso',
    subscription: 'Sottoscrizione',
  };
  return map[type] ?? type;
}

/**
 * Mappa stato a label italiano
 */
export function statusLabel(status: string): string {
  const map: Record<string, string> = {
    draft: 'Bozza',
    approved: 'Approvata',
    posted: 'Registrata',
    generated: 'Generata',
  };
  return map[status] ?? status;
}

/**
 * Colore badge per stato
 */
export function statusColor(status: string): string {
  switch (status) {
    case 'draft':
    case 'generated':
      return 'text-warning bg-warning-dim';
    case 'approved':
      return 'text-accent bg-accent-dim';
    case 'posted':
      return 'text-success bg-success-dim';
    default:
      return 'text-text-muted bg-surface';
  }
}
