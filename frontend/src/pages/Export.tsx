import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Download, FileSpreadsheet, FileText, Database } from 'lucide-react';
import api from '../api/client';

type ExportFormat = 'csv' | 'excel' | 'profis' | 'teamsystem';

const formats: { key: ExportFormat; label: string; description: string; icon: typeof FileText }[] = [
  { key: 'csv', label: 'CSV Generico', description: 'Export configurabile, compatibile con qualsiasi gestionale', icon: FileText },
  { key: 'excel', label: 'Excel Formattato', description: 'File .xlsx con formattazione e formule', icon: FileSpreadsheet },
  { key: 'profis', label: 'PROFIS (Sistemi)', description: 'Formato compatibile con PROFIS di Sistemi S.p.A.', icon: Database },
  { key: 'teamsystem', label: 'TeamSystem', description: 'Formato compatibile con TeamSystem', icon: Database },
];

export default function Export() {
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>('csv');
  const [hoveredCard, setHoveredCard] = useState<ExportFormat | null>(null);

  const exportMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.get(`/export/${selectedFormat}`, { responseType: 'blob' });
      const ext = selectedFormat === 'excel' ? 'xlsx' : 'csv';
      const blob = new Blob([data]);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `titoliengine_export_${new Date().toISOString().slice(0, 10)}.${ext}`;
      a.click();
      URL.revokeObjectURL(url);
    },
  });

  return (
    <div style={{ padding: 32, backgroundColor: 'var(--bg-primary)', minHeight: '100vh' }}>
      {/* Breadcrumb + Header */}
      <p style={{ fontSize: 13, color: 'var(--text-secondary)', fontWeight: 500, marginBottom: 4 }}>
        Dashboard / Export
      </p>
      <h1 style={{ fontSize: 32, fontWeight: 600, letterSpacing: '-0.02em', color: 'var(--text-primary)', margin: 0, marginBottom: 24 }}>
        Export
      </h1>

      {/* Format Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 16, marginBottom: 32 }}>
        {formats.map(({ key, label, description, icon: Icon }) => {
          const isSelected = selectedFormat === key;
          const isHovered = hoveredCard === key;

          return (
            <button
              key={key}
              onClick={() => setSelectedFormat(key)}
              onMouseEnter={() => setHoveredCard(key)}
              onMouseLeave={() => setHoveredCard(null)}
              style={{
                textAlign: 'left',
                backgroundColor: isHovered ? 'var(--bg-elevated)' : 'var(--bg-surface)',
                border: isSelected ? '2px solid var(--color-primary)' : '2px solid transparent',
                borderRadius: 24,
                padding: 20,
                cursor: 'pointer',
                boxShadow: isSelected ? 'var(--shadow-elevated)' : 'var(--shadow-neumorphic-out)',
                transition: 'all 0.2s',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
                <div
                  style={{
                    width: 40,
                    height: 40,
                    borderRadius: 12,
                    backgroundColor: isSelected ? 'rgba(10, 132, 255, 0.15)' : 'var(--bg-elevated)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    transition: 'all 0.2s',
                  }}
                >
                  <Icon size={20} style={{ color: isSelected ? 'var(--color-primary)' : 'var(--text-secondary)' }} />
                </div>
                <span style={{ fontWeight: 600, fontSize: 15, color: 'var(--text-primary)' }}>{label}</span>
              </div>
              <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>{description}</p>
            </button>
          );
        })}
      </div>

      {/* Export Button */}
      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <button
          onClick={() => exportMutation.mutate()}
          disabled={exportMutation.isPending}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            padding: '12px 28px',
            backgroundColor: 'var(--color-primary)',
            color: '#FFFFFF',
            border: 'none',
            borderRadius: 16,
            fontSize: 15,
            fontWeight: 600,
            cursor: exportMutation.isPending ? 'not-allowed' : 'pointer',
            opacity: exportMutation.isPending ? 0.5 : 1,
            boxShadow: '0 0 20px rgba(10, 132, 255, 0.4), var(--shadow-elevated)',
            transition: 'all 0.2s',
          }}
        >
          <Download size={18} />
          {exportMutation.isPending ? 'Esportazione...' : `Esporta ${formats.find(f => f.key === selectedFormat)?.label}`}
        </button>
      </div>
    </div>
  );
}
