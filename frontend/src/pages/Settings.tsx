import { Building2, User, Database } from 'lucide-react';

export default function Settings() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl mb-1">Impostazioni</h1>
        <p className="text-text-muted text-sm">Configurazione studio e preferenze</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-surface border border-border rounded-xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <Building2 size={20} className="text-primary" />
            <h3 className="text-lg">Studio</h3>
          </div>
          <div className="space-y-3">
            <Field label="Ragione Sociale" value="Studio Commercialista" />
            <Field label="Codice Fiscale" value="" placeholder="Inserisci..." />
            <Field label="Partita IVA" value="" placeholder="Inserisci..." />
          </div>
        </div>

        <div className="bg-surface border border-border rounded-xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <User size={20} className="text-accent" />
            <h3 className="text-lg">Profilo Utente</h3>
          </div>
          <div className="space-y-3">
            <Field label="Nome" value="" placeholder="Inserisci..." />
            <Field label="Email" value="" placeholder="Inserisci..." />
          </div>
        </div>

        <div className="bg-surface border border-border rounded-xl p-6 col-span-full">
          <div className="flex items-center gap-3 mb-4">
            <Database size={20} className="text-success" />
            <h3 className="text-lg">Database</h3>
          </div>
          <p className="text-sm text-text-muted">Connessione PostgreSQL configurata via variabili d'ambiente.</p>
        </div>
      </div>
    </div>
  );
}

function Field({ label, value, placeholder }: { label: string; value: string; placeholder?: string }) {
  return (
    <div>
      <label className="block text-xs text-text-muted mb-1">{label}</label>
      <input
        type="text"
        defaultValue={value}
        placeholder={placeholder}
        className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-text focus:outline-none focus:border-primary/50"
      />
    </div>
  );
}
