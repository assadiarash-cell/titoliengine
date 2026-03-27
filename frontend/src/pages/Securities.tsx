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
    {
      key: 'isin',
      header: 'ISIN',
      width: '140px',
      render: (s) => (
        <span
          style={{
            color: 'var(--color-primary)',
            fontFamily: 'var(--font-mono)',
            fontSize: '13px',
            fontWeight: 500,
          }}
        >
          {s.isin}
        </span>
      ),
    },
    { key: 'name', header: 'Denominazione' },
    {
      key: 'security_type',
      header: 'Tipo',
      width: '100px',
      render: (s) => (
        <span
          style={{
            display: 'inline-block',
            fontSize: '11px',
            fontWeight: 600,
            padding: '4px 10px',
            borderRadius: '8px',
            backgroundColor: 'var(--bg-elevated)',
            color: 'var(--text-secondary)',
          }}
        >
          {s.security_type}
        </span>
      ),
    },
    {
      key: 'coupon_rate',
      header: 'Cedola %',
      align: 'right',
      render: (s) =>
        s.coupon_rate ? (
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '13px' }}>
            {parseFloat(s.coupon_rate).toFixed(3)}%
          </span>
        ) : (
          <span style={{ color: 'var(--text-tertiary)' }}>&mdash;</span>
        ),
    },
    {
      key: 'face_value',
      header: 'Nominale',
      align: 'right',
      render: (s) => <MoneyDisplay value={s.face_value} />,
    },
    {
      key: 'maturity_date',
      header: 'Scadenza',
      render: (s) => (
        <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
          {formatDate(s.maturity_date)}
        </span>
      ),
      width: '110px',
    },
    {
      key: 'tax_regime',
      header: 'Regime',
      width: '100px',
      render: (s) => (
        <span
          style={{
            display: 'inline-block',
            fontSize: '11px',
            fontWeight: 600,
            padding: '4px 10px',
            borderRadius: '8px',
            backgroundColor:
              s.tax_regime === 'government'
                ? 'rgba(48, 209, 88, 0.15)'
                : 'rgba(255, 159, 10, 0.15)',
            color:
              s.tax_regime === 'government'
                ? 'var(--color-success)'
                : 'var(--color-warning)',
          }}
        >
          {s.tax_regime}
        </span>
      ),
    },
    {
      key: 'actions',
      header: '',
      sortable: false,
      width: '50px',
      render: (s) => (
        <button
          onClick={(e) => {
            e.stopPropagation();
            deleteMutation.mutate(s.id);
          }}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            color: 'var(--text-tertiary)',
            padding: '4px',
            borderRadius: '6px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'color 0.15s, background-color 0.15s',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = 'var(--color-danger)';
            e.currentTarget.style.backgroundColor = 'rgba(255, 69, 58, 0.1)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = 'var(--text-tertiary)';
            e.currentTarget.style.backgroundColor = 'transparent';
          }}
        >
          <X size={14} />
        </button>
      ),
    },
  ];

  return (
    <div
      style={{
        padding: '32px',
        backgroundColor: 'var(--bg-primary)',
        minHeight: '100%',
        fontFamily: 'var(--font-system)',
      }}
    >
      {/* Page Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          marginBottom: '28px',
        }}
      >
        <div>
          <p
            style={{
              fontSize: '13px',
              color: 'var(--text-secondary)',
              fontWeight: 500,
              marginBottom: '4px',
            }}
          >
            TitoliEngine &rsaquo; Titoli
          </p>
          <h1
            style={{
              fontSize: '32px',
              fontWeight: 600,
              letterSpacing: '-0.02em',
              color: 'var(--text-primary)',
              margin: 0,
            }}
          >
            Titoli
          </h1>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 24px',
            backgroundColor: 'var(--color-primary)',
            color: '#FFFFFF',
            border: 'none',
            borderRadius: '16px',
            fontSize: '14px',
            fontWeight: 600,
            cursor: 'pointer',
            boxShadow: '0 4px 16px rgba(10, 132, 255, 0.35)',
            transition: 'transform 0.15s, box-shadow 0.15s',
            fontFamily: 'var(--font-system)',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-1px)';
            e.currentTarget.style.boxShadow = '0 6px 20px rgba(10, 132, 255, 0.45)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = '0 4px 16px rgba(10, 132, 255, 0.35)';
          }}
        >
          <Plus size={16} />
          Nuovo Titolo
        </button>
      </div>

      {/* Security Form */}
      {showForm && <SecurityForm onClose={() => setShowForm(false)} />}

      {/* Search Input */}
      <div style={{ position: 'relative', marginBottom: '24px' }}>
        <Search
          size={16}
          style={{
            position: 'absolute',
            left: '16px',
            top: '50%',
            transform: 'translateY(-50%)',
            color: 'var(--text-tertiary)',
            pointerEvents: 'none',
          }}
        />
        <input
          type="text"
          placeholder="Cerca per ISIN o denominazione..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            width: '100%',
            paddingLeft: '44px',
            paddingRight: '16px',
            paddingTop: '14px',
            paddingBottom: '14px',
            backgroundColor: 'var(--bg-surface)',
            border: 'none',
            borderRadius: '16px',
            fontSize: '14px',
            color: 'var(--text-primary)',
            boxShadow: 'var(--shadow-neumorphic-in)',
            outline: 'none',
            fontFamily: 'var(--font-system)',
            boxSizing: 'border-box',
          }}
        />
      </div>

      {/* Data Table */}
      {isLoading ? (
        <div
          style={{
            textAlign: 'center',
            padding: '48px 0',
            color: 'var(--text-secondary)',
            fontSize: '14px',
          }}
        >
          Caricamento...
        </div>
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
    isin: '',
    name: '',
    security_type: 'BTP',
    currency: 'EUR',
    face_value: '100',
    coupon_rate: '',
    coupon_frequency: '2',
    maturity_date: '',
    issue_date: '',
    tax_regime: 'government',
    day_count_convention: 'ACT/ACT',
  });

  const mutation = useMutation({
    mutationFn: (data: typeof form) => api.post('/securities/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['securities'] });
      onClose();
    },
  });

  const field = (label: string, key: keyof typeof form, type = 'text') => (
    <div>
      <label
        style={{
          display: 'block',
          fontSize: '11px',
          fontWeight: 600,
          textTransform: 'uppercase' as const,
          letterSpacing: '0.08em',
          color: 'var(--text-tertiary)',
          marginBottom: '6px',
        }}
      >
        {label}
      </label>
      <input
        type={type}
        value={form[key]}
        onChange={(e) => setForm({ ...form, [key]: e.target.value })}
        style={{
          width: '100%',
          padding: '10px 14px',
          backgroundColor: 'var(--bg-primary)',
          border: '1px solid var(--border-default)',
          borderRadius: '12px',
          fontSize: '14px',
          color: 'var(--text-primary)',
          outline: 'none',
          fontFamily: 'var(--font-system)',
          boxSizing: 'border-box',
          transition: 'border-color 0.15s',
        }}
        onFocus={(e) => {
          e.currentTarget.style.borderColor = 'var(--color-primary)';
        }}
        onBlur={(e) => {
          e.currentTarget.style.borderColor = 'var(--border-default)';
        }}
      />
    </div>
  );

  return (
    <div
      style={{
        backgroundColor: 'var(--bg-surface)',
        borderRadius: '24px',
        padding: '28px',
        marginBottom: '24px',
        boxShadow: 'var(--shadow-neumorphic-out)',
      }}
    >
      {/* Form Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '24px',
        }}
      >
        <h3
          style={{
            fontSize: '18px',
            fontWeight: 600,
            color: 'var(--text-primary)',
            margin: 0,
          }}
        >
          Nuovo Titolo
        </h3>
        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            color: 'var(--text-tertiary)',
            padding: '4px',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'color 0.15s',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = 'var(--text-primary)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = 'var(--text-tertiary)';
          }}
        >
          <X size={18} />
        </button>
      </div>

      {/* Form Grid */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          mutation.mutate(form);
        }}
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: '16px',
        }}
      >
        {field('ISIN', 'isin')}
        {field('Denominazione', 'name')}
        {field('Tipo', 'security_type')}
        {field('Valuta', 'currency')}
        {field('Valore Nominale', 'face_value', 'number')}
        {field('Tasso Cedola %', 'coupon_rate', 'number')}
        {field('Frequenza Cedola', 'coupon_frequency', 'number')}
        {field('Regime Fiscale', 'tax_regime')}
        {field('Data Emissione', 'issue_date', 'date')}
        {field('Data Scadenza', 'maturity_date', 'date')}

        {/* Actions row spanning full width */}
        <div
          style={{
            gridColumn: '1 / -1',
            display: 'flex',
            justifyContent: 'flex-end',
            gap: '12px',
            marginTop: '8px',
          }}
        >
          <button
            type="button"
            onClick={onClose}
            style={{
              padding: '10px 20px',
              fontSize: '14px',
              fontWeight: 500,
              color: 'var(--text-secondary)',
              backgroundColor: 'transparent',
              border: '1px solid var(--border-default)',
              borderRadius: '12px',
              cursor: 'pointer',
              fontFamily: 'var(--font-system)',
              transition: 'color 0.15s, border-color 0.15s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = 'var(--text-primary)';
              e.currentTarget.style.borderColor = 'var(--text-tertiary)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = 'var(--text-secondary)';
              e.currentTarget.style.borderColor = 'var(--border-default)';
            }}
          >
            Annulla
          </button>
          <button
            type="submit"
            disabled={mutation.isPending}
            style={{
              padding: '10px 24px',
              fontSize: '14px',
              fontWeight: 600,
              color: '#FFFFFF',
              backgroundColor: 'var(--color-primary)',
              border: 'none',
              borderRadius: '16px',
              cursor: mutation.isPending ? 'not-allowed' : 'pointer',
              opacity: mutation.isPending ? 0.5 : 1,
              boxShadow: '0 4px 16px rgba(10, 132, 255, 0.35)',
              fontFamily: 'var(--font-system)',
              transition: 'transform 0.15s, box-shadow 0.15s',
            }}
            onMouseEnter={(e) => {
              if (!mutation.isPending) {
                e.currentTarget.style.transform = 'translateY(-1px)';
                e.currentTarget.style.boxShadow = '0 6px 20px rgba(10, 132, 255, 0.45)';
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 4px 16px rgba(10, 132, 255, 0.35)';
            }}
          >
            {mutation.isPending ? 'Salvataggio...' : 'Salva Titolo'}
          </button>
        </div>
      </form>
    </div>
  );
}
