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
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl mb-1">Report</h1>
          <p className="text-text-muted text-sm">Reportistica contabile e fiscale OIC 20</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2.5 bg-surface border border-border rounded-lg text-sm text-text-muted hover:text-text hover:bg-surface-hover transition-colors">
          <Download size={16} /> Esporta PDF
        </button>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 bg-surface border border-border rounded-lg p-1">
        {reportTabs.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm transition-colors ${
              activeTab === key ? 'bg-primary-dim text-primary font-medium' : 'text-text-muted hover:text-text'
            }`}
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
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Valore di Mercato', value: data?.total_value ?? '0' },
          { label: 'Costo Storico', value: data?.total_cost ?? '0' },
          { label: 'Plus/Minusvalenza', value: data?.total_gain ?? '0' },
        ].map(({ label, value }) => (
          <div key={label} className="bg-surface border border-border rounded-xl p-4">
            <span className="text-xs text-text-muted">{label}</span>
            <div className="mt-1"><MoneyDisplay value={value} className="text-xl" /></div>
          </div>
        ))}
      </div>
      {positions.length > 0 && (
        <div className="bg-surface border border-border rounded-xl p-6">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={positions}>
              <XAxis dataKey="name" tick={{ fill: '#8888A0', fontSize: 12 }} />
              <YAxis tick={{ fill: '#8888A0', fontSize: 12 }} />
              <Tooltip contentStyle={{ background: '#141419', border: '1px solid #1E1E2E', borderRadius: 8, color: '#F0F0F5' }} />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {positions.map((_: unknown, i: number) => (
                  <Cell key={i} fill={i % 2 === 0 ? '#C9A84C' : '#4A9EFF'} />
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
    <div className="bg-surface border border-border rounded-xl p-6">
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div><span className="text-xs text-text-muted">Plusvalenze</span><div className="mt-1 text-success font-money text-lg">€ {data?.total_gains ?? '0'}</div></div>
        <div><span className="text-xs text-text-muted">Minusvalenze</span><div className="mt-1 text-danger font-money text-lg">€ {data?.total_losses ?? '0'}</div></div>
        <div><span className="text-xs text-text-muted">Netto</span><div className="mt-1"><MoneyDisplay value={data?.net ?? '0'} className="text-lg" /></div></div>
      </div>
      <p className="text-text-muted text-sm">Seleziona un periodo per visualizzare il dettaglio delle operazioni chiuse.</p>
    </div>
  );
}

function TaxReport() {
  return (
    <div className="bg-surface border border-border rounded-xl p-6">
      <h3 className="text-lg mb-4">Riepilogo Ritenute Fiscali</h3>
      <div className="space-y-3">
        {[
          { label: 'Titoli di Stato (12,50%)', regime: 'government' },
          { label: 'Corporate Bond (26,00%)', regime: 'standard' },
          { label: 'Regime PEX (1,20%)', regime: 'pex' },
        ].map(({ label }) => (
          <div key={label} className="flex items-center justify-between px-4 py-3 bg-background rounded-lg">
            <span className="text-sm">{label}</span>
            <MoneyDisplay value="0" className="text-sm" />
          </div>
        ))}
      </div>
    </div>
  );
}

function NotaIntegrativaReport() {
  return (
    <div className="bg-surface border border-border rounded-xl p-6">
      <h3 className="text-lg mb-2">Dati per Nota Integrativa OIC 20</h3>
      <p className="text-text-muted text-sm mb-4">
        Prospetto delle variazioni dei titoli immobilizzati e dell'attivo circolante secondo il principio contabile OIC 20.
      </p>
      <div className="border border-border rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-surface-hover text-text-muted">
              <th className="text-left px-4 py-2">Voce</th>
              <th className="text-right px-4 py-2">Inizio Esercizio</th>
              <th className="text-right px-4 py-2">Acquisti</th>
              <th className="text-right px-4 py-2">Vendite/Rimborsi</th>
              <th className="text-right px-4 py-2">Rivalutazioni</th>
              <th className="text-right px-4 py-2">Svalutazioni</th>
              <th className="text-right px-4 py-2">Fine Esercizio</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-t border-border/50">
              <td className="px-4 py-3 text-text-muted" colSpan={7}>Nessun dato disponibile per l'esercizio corrente</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

function SocietaComodoReport() {
  return (
    <div className="bg-surface border border-border rounded-xl p-6">
      <h3 className="text-lg mb-2">Test Società di Comodo</h3>
      <p className="text-text-muted text-sm mb-4">
        Verifica art. 30 L. 724/1994 — confronto ricavi minimi presunti con ricavi effettivi.
      </p>
      <div className="p-4 bg-background rounded-lg border border-border text-center text-text-muted text-sm">
        Inserisci i dati patrimoniali per eseguire il test
      </div>
    </div>
  );
}
