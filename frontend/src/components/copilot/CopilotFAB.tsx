/**
 * CopilotFAB — Floating Action Button per aprire il Copilot.
 * Posizionato in basso a destra con design neomorphic.
 */
import { Cpu } from 'lucide-react';

interface CopilotFABProps {
  onClick: () => void;
  isOpen: boolean;
}

export default function CopilotFAB({ onClick, isOpen }: CopilotFABProps) {
  if (isOpen) return null;

  return (
    <button
      onClick={onClick}
      title="Apri Copilot"
      aria-label="Apri Copilot AI"
      style={{
        position: 'fixed',
        bottom: 24,
        right: 24,
        width: 56,
        height: 56,
        borderRadius: 18,
        border: 'none',
        background: 'linear-gradient(135deg, var(--color-primary), #5E5CE6)',
        boxShadow: '0 4px 20px rgba(10, 132, 255, 0.4), var(--shadow-neumorphic-out)',
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 997,
        transition: 'transform 0.2s, box-shadow 0.2s',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'scale(1.08)';
        e.currentTarget.style.boxShadow =
          '0 6px 28px rgba(10, 132, 255, 0.5), var(--shadow-neumorphic-out)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'scale(1)';
        e.currentTarget.style.boxShadow =
          '0 4px 20px rgba(10, 132, 255, 0.4), var(--shadow-neumorphic-out)';
      }}
    >
      <Cpu size={24} color="#FFFFFF" />
    </button>
  );
}
