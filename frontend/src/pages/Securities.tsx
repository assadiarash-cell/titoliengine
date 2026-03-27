import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Search, X } from 'lucide-react';
import api from '../api/client';
import DataTable, { type Column } from '../components/common/DataTable';
import MoneyDisplay from '../components/common/MoneyDisplay';
import { formatDate } from '../utils/formatters';
import type { Security } from '../types';

export default function Securities() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);

  const { data: securities = [], isLoading } = useQuery<Security[]>({
    queryKey: ['securities'],
    queryFn: async () => {
      const { data } = await api.get('/securities/');
      return Array.isArray(data) ? data : data.items ?? [];
    },
  });

  const filtered = securities.filter(
    (s) =>
      s.isin.toLowerCase().includes(search.toLowerCase()) ||
      s.name.toLowerCase().includes(search.toLowerCase())
  );

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/securities/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['securities'] }),
  });

  const columns: Column<Security>[] = [
    { key: 'isin', header: 'ISIN', width: '140px' },
    { key: 'name', header: 'Denominazione' },
    { key: 'security_type', header: 'Tipo', width: '100px' },
    {
      key: 'coupon_rate',
      header: 'Cedola %',
      align: 'right',
      render: (s) => s.coupon_rate ? <span className="font-money">{parseFloat(s.coupon_rate).toFixed(3)}%</span> : '—',
    },
    {
      key: 'face_value',
      header: 'Nominale',
      align: 'right',
      render: (s) => <MoneyDisplay value={s.face_value} />,
    },
    { key: 'maturity_date', header: 'Scadenza', render: (s) => formatDate(s.maturity_date), width: '110px' },
    { key: 'tax_regime', header: 'Regime', width: '100px' },
    {
      key: 'actions',
      header: '',
      sortable: false,
      width: '50px',
      render: (s) => (
        <button
          onClick={(e) => { e.stopPropagation(); deleteMutation.mutate(s.id); }}
          className="text-text-dim hover:text-danger transition-colors"
        >
          <X size={14} />
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl mb-1">Titoli</h1>
          <p className="text-text-muted text-sm">Anagrafica titoli obbligazionari</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-4 py-2.5 bg-primary text-background rounded-lg text-sm font-medium hover:bg-primary-hover transition-colors"
        >
          <Plus size={16} />
          Nuovo Titolo
        </button>
      </div>

      {showForm && <SecurityForm onClose={() => setShowForm(false)} />}

      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
        <input
          type="text"
          placeholder="Cerca per ISIN o denominazione..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 bg-surface border border-border rounded-lg text-sm text-text placeholder-text-dim focus:outline-none focus:border-primary/50"
        />
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-text-muted">Caricamento...</div>
      ) : (
        <DataTable
          columns={columns}
          data={filtered}
          keyExtractor={(s) => s.id}
          emptyMessage="Nessun titolo trovato"
        />
      )}
    </div>
  );
}

function SecurityForm({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({
    isin: '', name: '', security_type: 'BTP', currency: 'EUR',
    face_value: '100', coupon_rate: '', coupon_frequency: '2',
    maturity_date: '', issue_date: '', tax_regime: 'government',
    day_count_convention: 'ACT/ACT',
  });

  const mutation = useMutation({
    mutationFn: (data: typeof form) => api.post('/securities/', data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['securities'] }); onClose(); },
  });

  const field = (label: string, key: keyof typeof form, type = 'text', opts?: { half?: boolean }) => (
    <div className={opts?.half ? 'col-span-1' : 'col-span-2'}>
      <label className="block text-xs text-text-muted mb-1">{label}</label>
      <input
        type={type}
        value={form[key]}
        onChange={(e) => setForm({ ...form, [key]: e.target.value })}
        className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-text focus:outline-none focus:border-primary/50"
      />
    </div>
  );

  return (
    <div className="bg-surface border border-border rounded-xl p-6 animate-fade-in">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg">Nuovo Titolo</h3>
        <button onClick={onClose} className="text-text-muted hover:text-text"><X size={18} /></button>
      </div>
      <form
        onSubmit={(e) => { e.preventDefault(); mutation.mutate(form); }}
        className="grid grid-cols-2 sm:grid-cols-4 gap-4"
      >
        {field('ISIN', 'isin', 'text', { half: true })}
        {field('Denominazione', 'name', 'text', { half: true })}
        {field('Tipo', 'security_type', 'text', { half: true })}
        {field('Valuta', 'currency', 'text', { half: true })}
        {field('Valore Nominale', 'face_value', 'number', { half: true })}
        {field('Tasso Cedola %', 'coupon_rate', 'number', { half: true })}
        {field('Frequenza Cedola', 'coupon_frequency', 'number', { half: true })}
        {field('Regime Fiscale', 'tax_regime', 'text', { half: true })}
        {field('Data Emissione', 'issue_date', 'date', { half: true })}
        {field('Data Scadenza', 'maturity_date', 'date', { half: true })}
        <div className="col-span-full flex justify-end gap-3 mt-2">
          <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-text-muted hover:text-text">Annulla</button>
          <button
            type="submit"
            disabled={mutation.isPending}
            className="px-4 py-2.5 bg-primary text-background rounded-lg text-sm font-medium hover:bg-primary-hover disabled:opacity-50"
          >
            {mutation.isPending ? 'Salvataggio...' : 'Salva Titolo'}
          </button>
        </div>
      </form>
    </div>
  );
}
