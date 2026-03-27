import { Building2, User, Database } from 'lucide-react';

export default function Settings() {
  return (
    <div style={{ padding: 32, backgroundColor: 'var(--bg-primary)', minHeight: '100vh' }}>
      {/* Breadcrumb + Header */}
      <p style={{ fontSize: 13, color: 'var(--text-secondary)', fontWeight: 500, marginBottom: 4 }}>
        Dashboard / Impostazioni
      </p>
      <h1 style={{ fontSize: 32, fontWeight: 600, letterSpacing: '-0.02em', color: 'var(--text-primary)', margin: 0, marginBottom: 24 }}>
        Impostazioni
      </h1>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 24 }}>
        {/* Studio Card */}
        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            borderRadius: 24,
            padding: 24,
            boxShadow: 'var(--shadow-neumorphic-out)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
            <div
              style={{
                width: 36,
                height: 36,
                borderRadius: 10,
                backgroundColor: 'var(--bg-elevated)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Building2 size={18} style={{ color: 'var(--color-primary)' }} />
            </div>
            <h3 style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>Studio</h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <Field label="Ragione Sociale" value="Studio Commercialista" />
            <Field label="Codice Fiscale" value="" placeholder="Inserisci..." />
            <Field label="Partita IVA" value="" placeholder="Inserisci..." />
          </div>
        </div>

        {/* Profilo Utente Card */}
        <div
          style={{
            backgroundColor: 'var(--bg-surface)',
            borderRadius: 24,
            padding: 24,
            boxShadow: 'var(--shadow-neumorphic-out)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
            <div
              style={{
                width: 36,
                height: 36,
                borderRadius: 10,
                backgroundColor: 'var(--bg-elevated)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <User size={18} style={{ color: 'var(--color-warning)' }} />
            </div>
            <h3 style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>Profilo Utente</h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <Field label="Nome" value="" placeholder="Inserisci..." />
            <Field label="Email" value="" placeholder="Inserisci..." />
          </div>
        </div>

        {/* Database Card - full width */}
        <div
          style={{
            gridColumn: '1 / -1',
            backgroundColor: 'var(--bg-surface)',
            borderRadius: 24,
            padding: 24,
            boxShadow: 'var(--shadow-neumorphic-out)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
            <div
              style={{
                width: 36,
                height: 36,
                borderRadius: 10,
                backgroundColor: 'var(--bg-elevated)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Database size={18} style={{ color: 'var(--color-success)' }} />
            </div>
            <h3 style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>Database</h3>
          </div>
          <p style={{ fontSize: 14, color: 'var(--text-secondary)', margin: 0 }}>
            Connessione PostgreSQL configurata via variabili d'ambiente.
          </p>
        </div>
      </div>
    </div>
  );
}

function Field({ label, value, placeholder }: { label: string; value: string; placeholder?: string }) {
  return (
    <div>
      <label
        style={{
          display: 'block',
          fontSize: 11,
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
          color: 'var(--text-tertiary)',
          marginBottom: 6,
          fontWeight: 600,
        }}
      >
        {label}
      </label>
      <input
        type="text"
        defaultValue={value}
        placeholder={placeholder}
        style={{
          width: '100%',
          padding: '10px 14px',
          backgroundColor: 'var(--bg-primary)',
          border: 'none',
          borderRadius: 16,
          fontSize: 14,
          color: 'var(--text-primary)',
          boxShadow: 'var(--shadow-neumorphic-in)',
          outline: 'none',
          boxSizing: 'border-box',
        }}
      />
    </div>
  );
}
