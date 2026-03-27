export interface Studio {
  id: string;
  name: string;
  tax_code: string;
  created_at: string;
}

export interface Client {
  id: string;
  studio_id: string;
  name: string;
  tax_code: string;
  fiscal_year_end: string;
  chart_template: string;
  is_active: boolean;
  created_at: string;
}

export interface Security {
  id: string;
  isin: string;
  name: string;
  security_type: string;
  currency: string;
  face_value: string;
  coupon_rate: string | null;
  coupon_frequency: number | null;
  maturity_date: string;
  issue_date: string;
  tax_regime: string;
  day_count_convention: string;
  created_at: string;
}

export interface Transaction {
  id: string;
  client_id: string;
  security_id: string;
  transaction_type: string;
  trade_date: string;
  settlement_date: string;
  quantity: string;
  unit_price: string;
  accrued_interest: string;
  commission: string;
  stamp_duty: string;
  total_amount: string;
  status: 'draft' | 'approved' | 'posted';
  notes: string | null;
  created_at: string;
}

export interface JournalLine {
  id: string;
  account_code: string;
  account_name: string;
  debit: string;
  credit: string;
  description: string;
}

export interface JournalEntry {
  id: string;
  client_id: string;
  transaction_id: string | null;
  entry_date: string;
  entry_type: string;
  reference: string;
  description: string;
  status: 'generated' | 'approved' | 'posted';
  lines: JournalLine[];
  created_at: string;
}

export interface BalanceCheck {
  client_id: string;
  total_debit: string;
  total_credit: string;
  difference: string;
  is_balanced: boolean;
  entries_count: number;
}

export interface AuditLogEntry {
  id: number;
  entity_type: string;
  entity_id: string;
  action: string;
  user_id: string | null;
  changes: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
}

export interface QuickStatsData {
  securities_count: number;
  portfolio_value: string;
  pending_approvals: number;
  parsing_discrepancies: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
