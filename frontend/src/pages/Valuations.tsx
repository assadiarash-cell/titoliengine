import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { TrendingUp, Play, Calendar, AlertTriangle, Upload } from 'lucide-react';
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
    <div style={{ padding: '32px', background: 'var(--bg-primary)', minHeight: '100vh' }}>
      {/* Breadcrumb + Title */}
      <div style={{ marginBottom: '32px' }}>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
          Dashboard / Valutazioni
        </p>
        <h1
          style={{
            fontSize: '32px',
            fontWeight: 600,
            color: 'var(--text-primary)',
            margin: 0,
          }}
        >
          Valutazioni
        </h1>
      </div>

      {/* Cards grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Year-end valuation card */}
        <div
          style={{
            borderRadius: '24px',
            background: 'var(--bg-surface)',
            boxShadow: 'var(--shadow-neumorphic-out)',
            padding: '32px',
          }}
        >
          {/* Card header */}
          <div className="flex items-center gap-4" style={{ marginBottom: '28px' }}>
            <div
              style={{
                padding: '14px',
                borderRadius: '16px',
                background: 'rgba(10, 132, 255, 0.12)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <TrendingUp size={22} style={{ color: 'var(--color-primary)' }} />
            </div>
            <div>
              <h3
                style={{
                  fontSize: '18px',
                  fontWeight: 600,
                  color: 'var(--text-primary)',
                  margin: 0,
                }}
              >
                Valutazione Fine Esercizio
              </h3>
              <p
                style={{
                  fontSize: '13px',
                  color: 'var(--text-secondary)',
                  margin: '2px 0 0',
                }}
              >
                Genera scritture di svalutazione/ripristino OIC 20
              </p>
            </div>
          </div>

          {/* Input group */}
          <div style={{ marginBottom: '20px' }}>
            <label
              style={{
                display: 'block',
                fontSize: '12px',
                fontWeight: 600,
                color: 'var(--text-tertiary)',
                textTransform: 'uppercase' as const,
                letterSpacing: '0.06em',
                marginBottom: '8px',
              }}
            >
              Anno Esercizio
            </label>
            <div className="flex gap-3">
              <div className="relative flex-1">
                <Calendar
                  size={16}
                  className="absolute left-4 top-1/2 -translate-y-1/2"
                  style={{ color: 'var(--text-tertiary)' }}
                />
                <input
                  type="number"
                  value={yearEnd}
                  onChange={(e) => setYearEnd(e.target.value)}
                  min="2000"
                  max="2099"
                  style={{
                    width: '100%',
                    paddingLeft: '44px',
                    paddingRight: '16px',
                    paddingTop: '14px',
                    paddingBottom: '14px',
                    background: 'var(--bg-primary)',
                    border: 'none',
                    borderRadius: '16px',
                    boxShadow: 'var(--shadow-neumorphic-in)',
                    fontSize: '15px',
                    fontFamily: 'var(--font-mono)',
                    color: 'var(--text-primary)',
                    outline: 'none',
                  }}
                />
              </div>
              <button
                onClick={() => yearEndMutation.mutate()}
                disabled={yearEndMutation.isPending}
                className="flex items-center gap-2 disabled:opacity-50"
                style={{
                  padding: '14px 24px',
                  background: 'var(--color-primary)',
                  color: '#FFFFFF',
                  borderRadius: '16px',
                  border: 'none',
                  fontSize: '14px',
                  fontWeight: 600,
                  cursor: yearEndMutation.isPending ? 'not-allowed' : 'pointer',
                  boxShadow:
                    '0 0 20px rgba(10, 132, 255, 0.4), 0 4px 12px rgba(10, 132, 255, 0.3)',
                  transition: 'all 0.2s ease',
                  whiteSpace: 'nowrap' as const,
                }}
              >
                <Play size={16} />
                {yearEndMutation.isPending ? 'Elaborazione...' : 'Avvia'}
              </button>
            </div>
          </div>

          {/* Status messages */}
          {yearEndMutation.isSuccess && (
            <div
              className="flex items-center gap-2"
              style={{
                padding: '14px 18px',
                borderRadius: '16px',
                background: 'rgba(48, 209, 88, 0.1)',
                color: 'var(--color-success)',
                fontSize: '14px',
                fontWeight: 500,
              }}
            >
              <TrendingUp size={16} />
              Valutazione completata. Scritture generate.
            </div>
          )}
          {yearEndMutation.isError && (
            <div
              className="flex items-center gap-2"
              style={{
                padding: '14px 18px',
                borderRadius: '16px',
                background: 'rgba(255, 69, 58, 0.1)',
                color: 'var(--color-danger)',
                fontSize: '14px',
                fontWeight: 500,
              }}
            >
              <AlertTriangle size={16} />
              Errore durante la valutazione
            </div>
          )}
        </div>

        {/* Market prices import card */}
        <div
          style={{
            borderRadius: '24px',
            background: 'var(--bg-surface)',
            boxShadow: 'var(--shadow-neumorphic-out)',
            padding: '32px',
          }}
        >
          {/* Card header */}
          <div className="flex items-center gap-4" style={{ marginBottom: '28px' }}>
            <div
              style={{
                padding: '14px',
                borderRadius: '16px',
                background: 'rgba(48, 209, 88, 0.12)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <TrendingUp size={22} style={{ color: 'var(--color-success)' }} />
            </div>
            <div>
              <h3
                style={{
                  fontSize: '18px',
                  fontWeight: 600,
                  color: 'var(--text-primary)',
                  margin: 0,
                }}
              >
                Import Prezzi di Mercato
              </h3>
              <p
                style={{
                  fontSize: '13px',
                  color: 'var(--text-secondary)',
                  margin: '2px 0 0',
                }}
              >
                Carica file CSV con prezzi di chiusura
              </p>
            </div>
          </div>

          {/* Drop zone */}
          <div
            style={{
              borderRadius: '16px',
              padding: '40px 24px',
              textAlign: 'center',
              background: 'var(--bg-primary)',
              boxShadow: 'var(--shadow-neumorphic-in)',
              transition: 'all 0.3s ease',
            }}
          >
            <label style={{ cursor: 'pointer', display: 'block' }}>
              <Upload
                size={32}
                style={{
                  margin: '0 auto 12px',
                  display: 'block',
                  color: 'var(--text-tertiary)',
                }}
              />
              <p
                style={{
                  fontSize: '14px',
                  color: 'var(--text-secondary)',
                  marginBottom: '16px',
                }}
              >
                {importPricesMutation.isPending
                  ? 'Caricamento...'
                  : 'Trascina o seleziona file CSV'}
              </p>
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '12px 24px',
                  background: 'var(--color-primary)',
                  color: '#FFFFFF',
                  borderRadius: '16px',
                  fontSize: '14px',
                  fontWeight: 600,
                  boxShadow:
                    '0 0 20px rgba(10, 132, 255, 0.4), 0 4px 12px rgba(10, 132, 255, 0.3)',
                  transition: 'all 0.2s ease',
                }}
              >
                <Upload size={16} />
                Seleziona file
              </span>
              <input
                type="file"
                accept=".csv"
                className="hidden"
                style={{ display: 'none' }}
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) importPricesMutation.mutate(file);
                }}
              />
            </label>
          </div>

          {/* Status messages */}
          {importPricesMutation.isSuccess && (
            <div
              className="flex items-center gap-2"
              style={{
                padding: '14px 18px',
                borderRadius: '16px',
                background: 'rgba(48, 209, 88, 0.1)',
                color: 'var(--color-success)',
                fontSize: '14px',
                fontWeight: 500,
                marginTop: '20px',
              }}
            >
              <TrendingUp size={16} />
              Prezzi importati con successo.
            </div>
          )}
          {importPricesMutation.isError && (
            <div
              className="flex items-center gap-2"
              style={{
                padding: '14px 18px',
                borderRadius: '16px',
                background: 'rgba(255, 69, 58, 0.1)',
                color: 'var(--color-danger)',
                fontSize: '14px',
                fontWeight: 500,
                marginTop: '20px',
              }}
            >
              <AlertTriangle size={16} />
              Errore durante l'importazione
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
