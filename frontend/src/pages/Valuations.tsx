import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { TrendingUp, Play, Calendar, AlertTriangle } from 'lucide-react';
import api from '../api/client';

export default function Valuations() {
  const queryClient = useQueryClient();
  const [yearEnd, setYearEnd] = useState(new Date().getFullYear().toString());

  const yearEndMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post('/valuations/year-end', { year: parseInt(yearEnd) });
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['journal-entries'] }),
  });

  const importPricesMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      return api.post('/valuations/import-prices', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl mb-1">Valutazioni</h1>
        <p className="text-text-muted text-sm">Valutazione fine esercizio e import prezzi di mercato</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Year-end valuation */}
        <div className="bg-surface border border-border rounded-xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-lg bg-primary-dim">
              <TrendingUp size={20} className="text-primary" />
            </div>
            <div>
              <h3 className="text-lg">Valutazione Fine Esercizio</h3>
              <p className="text-xs text-text-muted">Genera scritture di svalutazione/ripristino OIC 20</p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-xs text-text-muted mb-1">Anno Esercizio</label>
              <div className="flex gap-3">
                <div className="relative flex-1">
                  <Calendar size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
                  <input
                    type="number"
                    value={yearEnd}
                    onChange={(e) => setYearEnd(e.target.value)}
                    min="2000" max="2099"
                    className="w-full pl-10 pr-4 py-2.5 bg-background border border-border rounded-lg text-sm text-text font-money focus:outline-none focus:border-primary/50"
                  />
                </div>
                <button
                  onClick={() => yearEndMutation.mutate()}
                  disabled={yearEndMutation.isPending}
                  className="flex items-center gap-2 px-4 py-2.5 bg-primary text-background rounded-lg text-sm font-medium hover:bg-primary-hover disabled:opacity-50"
                >
                  <Play size={16} />
                  {yearEndMutation.isPending ? 'Elaborazione...' : 'Avvia'}
                </button>
              </div>
            </div>

            {yearEndMutation.isSuccess && (
              <div className="flex items-center gap-2 px-4 py-3 rounded-lg border border-success/30 bg-success-dim text-success text-sm">
                <TrendingUp size={16} />
                Valutazione completata. Scritture generate.
              </div>
            )}
            {yearEndMutation.isError && (
              <div className="flex items-center gap-2 px-4 py-3 rounded-lg border border-danger/30 bg-danger-dim text-danger text-sm">
                <AlertTriangle size={16} />
                Errore durante la valutazione
              </div>
            )}
          </div>
        </div>

        {/* Market prices import */}
        <div className="bg-surface border border-border rounded-xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-lg bg-accent-dim">
              <TrendingUp size={20} className="text-accent" />
            </div>
            <div>
              <h3 className="text-lg">Import Prezzi di Mercato</h3>
              <p className="text-xs text-text-muted">Carica file CSV con prezzi di chiusura</p>
            </div>
          </div>

          <div
            className="border-2 border-dashed border-border rounded-lg p-6 text-center hover:border-border-light transition-colors"
          >
            <label className="cursor-pointer">
              <p className="text-sm text-text-muted mb-2">
                {importPricesMutation.isPending ? 'Caricamento...' : 'Trascina o seleziona file CSV'}
              </p>
              <span className="inline-block px-4 py-2 bg-background border border-border rounded-lg text-sm hover:bg-surface-hover">
                Seleziona file
              </span>
              <input
                type="file"
                accept=".csv"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) importPricesMutation.mutate(file);
                }}
              />
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}
