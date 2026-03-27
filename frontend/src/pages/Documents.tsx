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
    {
      key: 'filename',
      header: 'File',
      render: (d) => (
        <span className="flex items-center gap-2">
          <FileText size={14} style={{ color: 'var(--text-secondary)' }} />
          {d.filename}
        </span>
      ),
    },
    {
      key: 'status',
      header: 'Stato',
      width: '100px',
      render: (d) => (
        <span
          style={{
            display: 'inline-block',
            padding: '4px 12px',
            borderRadius: '12px',
            fontSize: '12px',
            fontWeight: 600,
            letterSpacing: '0.02em',
            background:
              d.status === 'parsed'
                ? 'rgba(48, 209, 88, 0.15)'
                : d.status === 'error'
                  ? 'rgba(255, 69, 58, 0.15)'
                  : 'rgba(255, 159, 10, 0.15)',
            color:
              d.status === 'parsed'
                ? 'var(--color-success)'
                : d.status === 'error'
                  ? 'var(--color-danger)'
                  : 'var(--color-warning)',
          }}
        >
          {d.status}
        </span>
      ),
    },
    {
      key: 'confidence',
      header: 'Confidence',
      align: 'right',
      width: '120px',
      render: (d) => {
        if (d.confidence == null) return '—';
        const pct = (d.confidence * 100).toFixed(0);
        const color =
          d.confidence >= 0.8
            ? 'var(--color-success)'
            : d.confidence >= 0.5
              ? 'var(--color-warning)'
              : 'var(--color-danger)';
        return (
          <span style={{ fontFamily: 'var(--font-mono)', color, fontWeight: 600 }}>
            {pct}%
          </span>
        );
      },
    },
    {
      key: 'created_at',
      header: 'Caricato',
      render: (d) => (
        <span style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
          {formatDateTime(d.created_at)}
        </span>
      ),
      width: '160px',
    },
  ];

  return (
    <div style={{ padding: '32px', background: 'var(--bg-primary)', minHeight: '100vh' }}>
      {/* Breadcrumb + Title */}
      <div style={{ marginBottom: '32px' }}>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
          Dashboard / Documenti
        </p>
        <h1
          style={{
            fontSize: '32px',
            fontWeight: 600,
            color: 'var(--text-primary)',
            margin: 0,
          }}
        >
          Documenti
        </h1>
      </div>

      {/* Drop zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        style={{
          borderRadius: '24px',
          padding: '48px 32px',
          textAlign: 'center',
          background: dragOver ? 'rgba(10, 132, 255, 0.08)' : 'var(--bg-surface)',
          boxShadow: 'var(--shadow-neumorphic-out)',
          border: `2px dashed ${dragOver ? 'var(--color-primary)' : 'var(--border-default)'}`,
          transition: 'all 0.3s ease',
          marginBottom: '32px',
          cursor: 'pointer',
        }}
      >
        <Upload
          size={40}
          style={{
            margin: '0 auto 16px',
            display: 'block',
            color: dragOver ? 'var(--color-primary)' : 'var(--text-tertiary)',
            transition: 'color 0.3s ease',
          }}
        />
        <p
          style={{
            fontSize: '15px',
            color: 'var(--text-secondary)',
            marginBottom: '16px',
          }}
        >
          {uploadMutation.isPending
            ? 'Caricamento in corso...'
            : 'Trascina qui il PDF del fissato bollato'}
        </p>
        <label
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
            cursor: 'pointer',
            boxShadow: '0 0 20px rgba(10, 132, 255, 0.4), 0 4px 12px rgba(10, 132, 255, 0.3)',
            transition: 'all 0.2s ease',
          }}
        >
          <Upload size={16} />
          <span>Seleziona file</span>
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileSelect}
            className="hidden"
            style={{ display: 'none' }}
          />
        </label>

        {uploadMutation.isSuccess && (
          <p
            className="flex items-center justify-center gap-2"
            style={{
              marginTop: '16px',
              fontSize: '14px',
              color: 'var(--color-success)',
            }}
          >
            <CheckCircle size={16} /> Documento caricato con successo
          </p>
        )}
        {uploadMutation.isError && (
          <p
            className="flex items-center justify-center gap-2"
            style={{
              marginTop: '16px',
              fontSize: '14px',
              color: 'var(--color-danger)',
            }}
          >
            <AlertTriangle size={16} /> Errore durante il caricamento
          </p>
        )}
      </div>

      {/* Documents table */}
      {isLoading ? (
        <div
          style={{
            textAlign: 'center',
            padding: '48px 0',
            color: 'var(--text-secondary)',
            fontSize: '15px',
          }}
        >
          Caricamento...
        </div>
      ) : (
        <DataTable
          columns={columns}
          data={documents}
          keyExtractor={(d) => d.id}
          emptyMessage="Nessun documento caricato"
        />
      )}
    </div>
  );
}
