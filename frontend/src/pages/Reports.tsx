import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { BarChart3, Download, FileText, Calculator, Scale, Building2 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import api from '../api/client';
import MoneyDisplay from '../components/common/MoneyDisplay';

type ReportType = 'portfolio' | 'gains_losses' | 'tax' | 'nota_integrativa' | 'societa_comodo';

const reportTabs: { key: ReportType; label: string; icon: typeof BarChart3 }[] = [
  { key: 'portfolio', label: 'Portafoglio', icon: BarChart3 },
  { key: 'gains_losses', label: 'Plus/Minus', icon: Calculator },
  { key: 'tax', label: 'Riepilogo Fiscale', icon: Scale },
  { key: 'nota_integrativa', label: 'Nota Integrativa', icon: FileText },
  { key: 'societa_comodo', label: 'Soc. Comodo', icon: Building2 },
];

export default function Reports() {
  const [activeTab, setActiveTab] = useState<ReportType>('portfolio');

  return (
    <div style={{ padding: 32, backgroundColor: 'var(--bg-primary)', minHeight: '100vh' }}>
      {/* Breadcrumb + Header */}
      <p style={{ fontSize: 13, color: 'var(--text-secondary)', fontWeight: 500, marginBottom: 4 }}>
        Dashboard / Report
      </p>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <h1 style={{ fontSize: 32, fontWeight: 600, letterSpacing: '-0.02em', color: 'var(--text-primary)', margin: 0 }}>
          Report
        </h1>
        <button
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            padding: '10px 20px',
            backgroundColor: 'var(--bg-surface)',
            color: 'var(--text-secondary)',
            border: 'none',
            borderRadius: 16,
            fontSize: 14,
            fontWeight: 500,
            cursor: 'pointer',
            boxShadow: 'var(--shadow-neumorphic-out)',
            transition: 'all 0.2s',
          }}
        >
          <Download size={16} /> Esporta PDF
        </button>
      </div>

      {/* Tab bar */}
      <div
        style={{
          display: 'flex',
          gap: 4,
          backgroundColor: 'var(--bg-surface)',
          borderRadius: 16,
          padding: 4,
          boxShadow: 'var(--shadow-neumorphic-out)',
          marginBottom: 24,
        }}
      >
        {reportTabs.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '10px 18px',
              borderRadius: 12,
              fontSize: 14,
              fontWeight: activeTab === key ? 600 : 400,
              border: 'none',
              cursor: 'pointer',
              transition: 'all 0.2s',
              backgroundColor: activeTab === key ? 'transparent' : 'transparent',
              color: activeTab === key ? 'var(--color-primary)' : 'var(--text-secondary)',
              boxShadow: activeTab === key ? 'var(--shadow-neumorphic-in)' : 'none',
            }}
          >
            <Icon size={16} />
            {label}
          </button>
        ))}
      </div>

      {activeTab === 'portfolio' && <PortfolioReport />}
      {activeTab === 'gains_losses' && <GainsLossesReport />}
      {activeTab === 'tax' && <TaxReport />}
      {activeTab === 'nota_integrativa' && <NotaIntegrativaReport />}
      {activeTab === 'societa_comodo' && <SocietaComodoReport />}
    </div>
  );
}

function PortfolioReport() {
  const { data } = useQuery({
    queryKey: ['report-portfolio'],
    queryFn: async () => {
      try {
        const { data } = await api.get('/reports/portfolio');
        return data;
      } catch {
        return { positions: [], total_value: '0', total_cost: '0', total_gain: '0' };
      }
    },
  });

  const positions = data?.positions ?? [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
        {[
          { label: 'Valore di Mercato', value: data?.total_value ?? '0' },
          { label: 'Costo Storico', value: data?.total_cost ?? '0' },
          { label: 'Plus/Minusvalenza', value: data?.total_gain ?? '0' },
        ].map(({ label, value }) => (
          <div
            key={label}
            style={{
              backgroundColor: 'var(--bg-surface)',
              borderRadius: 24,
              padding: 20,
              boxShadow: 'var(--shadow-neumorphic-out)',
            }}
          >
            <span style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-tertiary)' }}>
              {label}
            </span>
            <div style={{ marginTop: 8 }}>
              <MoneyDisplay value={value} className="text-xl" />
            </div>
          </div>
        ))}
      </div>
      {positions.length > 0 && (
        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            borderRadius: 24,
            padding: 24,
            boxShadow: 'var(--shadow-neumorphic-out)',
          }}
        >
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={positions}>
              <XAxis dataKey="name" tick={{ fill: 'var(--text-tertiary)', fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: 'var(--text-tertiary)', fontSize: 12 }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{
                  background: 'var(--bg-elevated)',
                  border: 'none',
                  borderRadius: 16,
                  color: 'var(--text-primary)',
                  boxShadow: 'var(--shadow-elevated)',
                }}
              />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {positions.map((_: unknown, i: number) => (
                  <Cell key={i} fill={i % 2 === 0 ? '#0A84FF' : '#30D158'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

function GainsLossesReport() {
  const { data } = useQuery({
    queryKey: ['report-gains-losses'],
    queryFn: async () => {
      try {
        const { data } = await api.get('/reports/gains-losses');
        return data;
      } catch {
        return { realized: [], total_gains: '0', total_losses: '0', net: '0' };
      }
    },
  });

  return (
    <div
      style={{
        backgroundColor: 'var(--bg-surface)',
        borderRadius: 24,
        padding: 24,
        boxShadow: 'var(--shadow-neumorphic-out)',
      }}
    >
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 24 }}>
        <div>
          <span style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-tertiary)' }}>
            Plusvalenze
          </span>
          <div style={{ marginTop: 8, color: 'var(--color-success)', fontFamily: 'var(--font-mono)', fontSize: 18 }}>
            {'\u20AC'} {data?.total_gains ?? '0'}
          </div>
        </div>
        <div>
          <span style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-tertiary)' }}>
            Minusvalenze
          </span>
          <div style={{ marginTop: 8, color: 'var(--color-danger)', fontFamily: 'var(--font-mono)', fontSize: 18 }}>
            {'\u20AC'} {data?.total_losses ?? '0'}
          </div>
        </div>
        <div>
          <span style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-tertiary)' }}>
            Netto
          </span>
          <div style={{ marginTop: 8 }}>
            <MoneyDisplay value={data?.net ?? '0'} className="text-lg" />
          </div>
        </div>
      </div>
      <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>
        Seleziona un periodo per visualizzare il dettaglio delle operazioni chiuse.
      </p>
    </div>
  );
}

function TaxReport() {
  return (
    <div
      style={{
        backgroundColor: 'var(--bg-surface)',
        borderRadius: 24,
        padding: 24,
        boxShadow: 'var(--shadow-neumorphic-out)',
      }}
    >
      <h3 style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 16, marginTop: 0 }}>
        Riepilogo Ritenute Fiscali
      </h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {[
          { label: 'Titoli di Stato (12,50%)', regime: 'government' },
          { label: 'Corporate Bond (26,00%)', regime: 'standard' },
          { label: 'Regime PEX (1,20%)', regime: 'pex' },
        ].map(({ label }) => (
          <div
            key={label}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '12px 16px',
              backgroundColor: 'var(--bg-primary)',
              borderRadius: 16,
              boxShadow: 'var(--shadow-neumorphic-in)',
            }}
          >
            <span style={{ fontSize: 14, color: 'var(--text-primary)' }}>{label}</span>
            <MoneyDisplay value="0" className="text-sm" />
          </div>
        ))}
      </div>
    </div>
  );
}

function NotaIntegrativaReport() {
  const headers = ['Voce', 'Inizio Esercizio', 'Acquisti', 'Vendite/Rimborsi', 'Rivalutazioni', 'Svalutazioni', 'Fine Esercizio'];

  return (
    <div
      style={{
        backgroundColor: 'var(--bg-surface)',
        borderRadius: 24,
        padding: 24,
        boxShadow: 'var(--shadow-neumorphic-out)',
      }}
    >
      <h3 style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8, marginTop: 0 }}>
        Dati per Nota Integrativa OIC 20
      </h3>
      <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 16 }}>
        Prospetto delle variazioni dei titoli immobilizzati e dell'attivo circolante secondo il principio contabile OIC 20.
      </p>
      <div style={{ borderRadius: 16, overflow: 'hidden' }}>
        <table style={{ width: '100%', fontSize: 14, borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              {headers.map((h, i) => (
                <th
                  key={h}
                  style={{
                    textAlign: i === 0 ? 'left' : 'right',
                    padding: '10px 16px',
                    fontSize: 11,
                    textTransform: 'uppercase',
                    letterSpacing: '0.08em',
                    color: 'var(--text-tertiary)',
                    backgroundColor: 'var(--bg-elevated)',
                    fontWeight: 600,
                    borderBottom: '1px solid var(--border-default)',
                  }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              <td
                colSpan={7}
                style={{
                  padding: '16px',
                  color: 'var(--text-secondary)',
                  textAlign: 'center',
                }}
              >
                Nessun dato disponibile per l'esercizio corrente
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

function SocietaComodoReport() {
  return (
    <div
      style={{
        backgroundColor: 'var(--bg-surface)',
        borderRadius: 24,
        padding: 24,
        boxShadow: 'var(--shadow-neumorphic-out)',
      }}
    >
      <h3 style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8, marginTop: 0 }}>
        Test Società di Comodo
      </h3>
      <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 16 }}>
        Verifica art. 30 L. 724/1994 — confronto ricavi minimi presunti con ricavi effettivi.
      </p>
      <div
        style={{
          padding: 20,
          backgroundColor: 'var(--bg-primary)',
          borderRadius: 16,
          boxShadow: 'var(--shadow-neumorphic-in)',
          textAlign: 'center',
          color: 'var(--text-secondary)',
          fontSize: 14,
        }}
      >
        Inserisci i dati patrimoniali per eseguire il test
      </div>
    </div>
  );
}
