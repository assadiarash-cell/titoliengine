import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Upload, FileText, CheckCircle, AlertTriangle } from 'lucide-react';
import api from '../api/client';
import DataTable, { type Column } from '../components/common/DataTable';
import { formatDateTime } from '../utils/formatters';

interface Document {
  id: string;
  filename: string;
  file_hash: string;
  content_type: string;
  status: string;
  confidence: number | null;
  parsed_data: Record<string, unknown> | null;
  created_at: string;
}

export default function Documents() {
  const queryClient = useQueryClient();
  const [dragOver, setDragOver] = useState(false);

  const { data: documents = [], isLoading } = useQuery<Document[]>({
    queryKey: ['documents'],
    queryFn: async () => {
      const { data } = await api.get('/documents/');
      return Array.isArray(data) ? data : data.items ?? [];
    },
  });

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      const { data } = await api.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['documents'] }),
  });

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) uploadMutation.mutate(file);
  }, [uploadMutation]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadMutation.mutate(file);
  }, [uploadMutation]);

  const columns: Column<Document>[] = [
    { key: 'filename', header: 'File', render: (d) => (
      <span className="flex items-center gap-2"><FileText size={14} className="text-text-muted" />{d.filename}</span>
    )},
    { key: 'status', header: 'Stato', width: '100px' },
    {
      key: 'confidence',
      header: 'Confidence',
      align: 'right',
      width: '120px',
      render: (d) => {
        if (d.confidence == null) return '—';
        const pct = (d.confidence * 100).toFixed(0);
        const color = d.confidence >= 0.8 ? 'text-success' : d.confidence >= 0.5 ? 'text-warning' : 'text-danger';
        return <span className={`font-money ${color}`}>{pct}%</span>;
      },
    },
    { key: 'created_at', header: 'Caricato', render: (d) => formatDateTime(d.created_at), width: '160px' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl mb-1">Documenti</h1>
        <p className="text-text-muted text-sm">Upload e parsing automatico fissati bollati</p>
      </div>

      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
          dragOver ? 'border-primary bg-primary-dim' : 'border-border hover:border-border-light'
        }`}
      >
        <Upload size={32} className={`mx-auto mb-3 ${dragOver ? 'text-primary' : 'text-text-dim'}`} />
        <p className="text-sm text-text-muted mb-2">
          {uploadMutation.isPending ? 'Caricamento in corso...' : 'Trascina qui il PDF del fissato bollato'}
        </p>
        <label className="inline-flex items-center gap-2 px-4 py-2 bg-surface border border-border rounded-lg text-sm cursor-pointer hover:bg-surface-hover">
          <span>Seleziona file</span>
          <input type="file" accept=".pdf" onChange={handleFileSelect} className="hidden" />
        </label>
        {uploadMutation.isSuccess && (
          <p className="mt-3 text-sm text-success flex items-center justify-center gap-2">
            <CheckCircle size={14} /> Documento caricato con successo
          </p>
        )}
        {uploadMutation.isError && (
          <p className="mt-3 text-sm text-danger flex items-center justify-center gap-2">
            <AlertTriangle size={14} /> Errore durante il caricamento
          </p>
        )}
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-text-muted">Caricamento...</div>
      ) : (
        <DataTable columns={columns} data={documents} keyExtractor={(d) => d.id} />
      )}
    </div>
  );
}
