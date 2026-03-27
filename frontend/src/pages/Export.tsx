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
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl mb-1">Export</h1>
        <p className="text-text-muted text-sm">Esportazione dati verso gestionali esterni</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {formats.map(({ key, label, description, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setSelectedFormat(key)}
            className={`text-left bg-surface border rounded-xl p-5 transition-colors card-hover ${
              selectedFormat === key ? 'border-primary' : 'border-border'
            }`}
          >
            <div className="flex items-center gap-3 mb-2">
              <div className={`p-2 rounded-lg ${selectedFormat === key ? 'bg-primary-dim text-primary' : 'bg-surface-hover text-text-muted'}`}>
                <Icon size={20} />
              </div>
              <span className="font-medium">{label}</span>
            </div>
            <p className="text-sm text-text-muted">{description}</p>
          </button>
        ))}
      </div>

      <div className="flex justify-end">
        <button
          onClick={() => exportMutation.mutate()}
          disabled={exportMutation.isPending}
          className="flex items-center gap-2 px-6 py-3 bg-primary text-background rounded-lg font-medium hover:bg-primary-hover disabled:opacity-50 transition-colors"
        >
          <Download size={18} />
          {exportMutation.isPending ? 'Esportazione...' : `Esporta ${formats.find(f => f.key === selectedFormat)?.label}`}
        </button>
      </div>
    </div>
  );
}
