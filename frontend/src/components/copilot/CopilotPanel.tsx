/**
 * CopilotPanel — Pannello slide-in laterale con chatbot AI.
 * Design: dark neomorphic coerente con il tema TitoliEngine.
 */
import { useState, useRef, useEffect } from 'react';
import {
  X,
  Send,
  Mic,
  MicOff,
  Trash2,
  Square,
  Cpu,
  Wrench,
} from 'lucide-react';
import { useCopilot, type CopilotMessage } from './useCopilot';
import { useVoiceInput } from './useVoiceInput';

interface CopilotPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

function ToolBadge({ name }: { name: string }) {
  const labels: Record<string, string> = {
    search_securities: 'Ricerca Titoli',
    get_dashboard_stats: 'Statistiche',
    list_transactions: 'Operazioni',
    get_journal_entries: 'Scritture',
    get_valuations: 'Valutazioni',
    get_audit_log: 'Audit Log',
    navigate_page: 'Navigazione',
    explain_concept: 'Spiegazione',
  };
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 4,
        padding: '2px 8px',
        borderRadius: 8,
        fontSize: 11,
        fontWeight: 600,
        letterSpacing: '0.02em',
        backgroundColor: 'rgba(10, 132, 255, 0.15)',
        color: 'var(--color-primary)',
      }}
    >
      <Wrench size={10} />
      {labels[name] || name}
    </span>
  );
}

function MessageBubble({ message }: { message: CopilotMessage }) {
  const isUser = message.role === 'user';
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: isUser ? 'flex-end' : 'flex-start',
        marginBottom: 12,
      }}
    >
      {/* Tool calls */}
      {message.toolCalls?.map((tc, i) => (
        <div key={i} style={{ marginBottom: 4 }}>
          <ToolBadge name={tc.name} />
        </div>
      ))}

      <div
        style={{
          maxWidth: '85%',
          padding: '10px 14px',
          borderRadius: isUser ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
          backgroundColor: isUser
            ? 'var(--color-primary)'
            : 'var(--bg-surface)',
          boxShadow: isUser
            ? 'none'
            : 'var(--shadow-neumorphic-subtle)',
          color: isUser ? '#FFFFFF' : 'var(--text-primary)',
          fontSize: 14,
          lineHeight: 1.5,
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
        }}
      >
        {message.content}
        {message.isStreaming && (
          <span
            style={{
              display: 'inline-block',
              width: 6,
              height: 14,
              marginLeft: 2,
              backgroundColor: 'var(--color-primary)',
              animation: 'blink 1s infinite',
              borderRadius: 1,
              verticalAlign: 'text-bottom',
            }}
          />
        )}
      </div>

      <span
        style={{
          fontSize: 10,
          color: 'var(--text-tertiary)',
          marginTop: 2,
          paddingLeft: isUser ? 0 : 4,
          paddingRight: isUser ? 4 : 0,
        }}
      >
        {message.timestamp.toLocaleTimeString('it-IT', {
          hour: '2-digit',
          minute: '2-digit',
        })}
      </span>
    </div>
  );
}

export default function CopilotPanel({ isOpen, onClose }: CopilotPanelProps) {
  const { messages, isLoading, sendMessage, clearChat, stopStreaming } =
    useCopilot();
  const { isListening, transcript, isSupported, startListening, stopListening } =
    useVoiceInput();

  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when panel opens
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 300);
    }
  }, [isOpen]);

  // Update input with voice transcript
  useEffect(() => {
    if (transcript) setInput(transcript);
  }, [transcript]);

  const handleSend = () => {
    const text = input.trim();
    if (!text || isLoading) return;
    setInput('');
    sendMessage(text);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleVoice = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening((text) => {
        setInput(text);
      });
    }
  };

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0,0,0,0.3)',
            zIndex: 998,
            transition: 'opacity 0.3s',
          }}
        />
      )}

      {/* Panel */}
      <div
        style={{
          position: 'fixed',
          top: 0,
          right: 0,
          bottom: 0,
          width: 420,
          maxWidth: '100vw',
          backgroundColor: 'var(--bg-primary)',
          borderLeft: '1px solid var(--border-default)',
          boxShadow: isOpen ? '-8px 0 24px rgba(0,0,0,0.5)' : 'none',
          zIndex: 999,
          display: 'flex',
          flexDirection: 'column',
          transform: isOpen ? 'translateX(0)' : 'translateX(100%)',
          transition: 'transform 0.3s ease-in-out',
        }}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '16px 20px',
            borderBottom: '1px solid var(--border-default)',
            backgroundColor: 'var(--bg-surface)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div
              style={{
                width: 36,
                height: 36,
                borderRadius: 10,
                background: 'linear-gradient(135deg, var(--color-primary), #5E5CE6)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: 'var(--shadow-neumorphic-subtle)',
              }}
            >
              <Cpu size={18} color="#fff" />
            </div>
            <div>
              <div
                style={{
                  fontSize: 15,
                  fontWeight: 600,
                  color: 'var(--text-primary)',
                }}
              >
                Copilot
              </div>
              <div
                style={{
                  fontSize: 11,
                  color: 'var(--text-tertiary)',
                }}
              >
                AI Assistant
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 4 }}>
            <button
              onClick={clearChat}
              title="Pulisci chat"
              style={{
                background: 'none',
                border: 'none',
                padding: 8,
                borderRadius: 8,
                cursor: 'pointer',
                color: 'var(--text-tertiary)',
                display: 'flex',
                alignItems: 'center',
              }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.backgroundColor = 'var(--bg-elevated)')
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.backgroundColor = 'transparent')
              }
            >
              <Trash2 size={16} />
            </button>
            <button
              onClick={onClose}
              style={{
                background: 'none',
                border: 'none',
                padding: 8,
                borderRadius: 8,
                cursor: 'pointer',
                color: 'var(--text-tertiary)',
                display: 'flex',
                alignItems: 'center',
              }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.backgroundColor = 'var(--bg-elevated)')
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.backgroundColor = 'transparent')
              }
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '16px 16px 8px',
          }}
        >
          {messages.length === 0 && (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                gap: 16,
                opacity: 0.6,
              }}
            >
              <div
                style={{
                  width: 64,
                  height: 64,
                  borderRadius: 20,
                  background:
                    'linear-gradient(135deg, var(--color-primary), #5E5CE6)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: 'var(--shadow-neumorphic-out)',
                }}
              >
                <Cpu size={28} color="#fff" />
              </div>
              <div style={{ textAlign: 'center' }}>
                <div
                  style={{
                    fontSize: 16,
                    fontWeight: 600,
                    color: 'var(--text-primary)',
                    marginBottom: 4,
                  }}
                >
                  Ciao! Sono il Copilot di TitoliEngine
                </div>
                <div
                  style={{
                    fontSize: 13,
                    color: 'var(--text-secondary)',
                    maxWidth: 280,
                    lineHeight: 1.5,
                  }}
                >
                  Posso aiutarti a cercare titoli, consultare operazioni,
                  spiegare concetti OIC 20 e molto altro.
                </div>
              </div>
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 6,
                  width: '100%',
                  maxWidth: 300,
                }}
              >
                {[
                  'Quanti titoli abbiamo in portafoglio?',
                  "Cos'è il costo ammortizzato?",
                  'Mostrami le operazioni in bozza',
                ].map((q) => (
                  <button
                    key={q}
                    onClick={() => sendMessage(q)}
                    style={{
                      padding: '10px 14px',
                      borderRadius: 12,
                      border: '1px solid var(--border-default)',
                      backgroundColor: 'var(--bg-surface)',
                      color: 'var(--text-secondary)',
                      fontSize: 13,
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'all 0.15s',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = 'var(--color-primary)';
                      e.currentTarget.style.color = 'var(--text-primary)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = 'var(--border-default)';
                      e.currentTarget.style.color = 'var(--text-secondary)';
                    }}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div
          style={{
            padding: '12px 16px 16px',
            borderTop: '1px solid var(--border-default)',
            backgroundColor: 'var(--bg-surface)',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'flex-end',
              gap: 8,
              padding: '8px 12px',
              borderRadius: 16,
              backgroundColor: 'var(--bg-primary)',
              boxShadow: 'var(--shadow-neumorphic-in)',
            }}
          >
            {/* Voice button */}
            {isSupported && (
              <button
                onClick={handleVoice}
                title={isListening ? 'Stop registrazione' : 'Input vocale'}
                style={{
                  background: 'none',
                  border: 'none',
                  padding: 6,
                  borderRadius: 8,
                  cursor: 'pointer',
                  color: isListening
                    ? 'var(--color-danger)'
                    : 'var(--text-tertiary)',
                  display: 'flex',
                  alignItems: 'center',
                  animation: isListening ? 'pulse 1.5s infinite' : 'none',
                }}
              >
                {isListening ? <MicOff size={18} /> : <Mic size={18} />}
              </button>
            )}

            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                isListening ? 'Sto ascoltando...' : 'Scrivi un messaggio...'
              }
              rows={1}
              style={{
                flex: 1,
                background: 'none',
                border: 'none',
                outline: 'none',
                color: 'var(--text-primary)',
                fontSize: 14,
                fontFamily: 'var(--font-system)',
                resize: 'none',
                maxHeight: 100,
                lineHeight: 1.4,
              }}
              onInput={(e) => {
                const el = e.currentTarget;
                el.style.height = 'auto';
                el.style.height = Math.min(el.scrollHeight, 100) + 'px';
              }}
            />

            {/* Send / Stop button */}
            {isLoading ? (
              <button
                onClick={stopStreaming}
                title="Ferma risposta"
                style={{
                  background: 'none',
                  border: 'none',
                  padding: 6,
                  borderRadius: 8,
                  cursor: 'pointer',
                  color: 'var(--color-danger)',
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                <Square size={18} />
              </button>
            ) : (
              <button
                onClick={handleSend}
                disabled={!input.trim()}
                title="Invia"
                style={{
                  background: input.trim()
                    ? 'var(--color-primary)'
                    : 'transparent',
                  border: 'none',
                  padding: 6,
                  borderRadius: 8,
                  cursor: input.trim() ? 'pointer' : 'default',
                  color: input.trim() ? '#FFFFFF' : 'var(--text-tertiary)',
                  display: 'flex',
                  alignItems: 'center',
                  transition: 'all 0.15s',
                }}
              >
                <Send size={18} />
              </button>
            )}
          </div>

          {isListening && (
            <div
              style={{
                marginTop: 6,
                fontSize: 11,
                color: 'var(--color-danger)',
                display: 'flex',
                alignItems: 'center',
                gap: 4,
              }}
            >
              <span
                style={{
                  width: 6,
                  height: 6,
                  borderRadius: '50%',
                  backgroundColor: 'var(--color-danger)',
                  animation: 'pulse 1s infinite',
                }}
              />
              Registrazione in corso...
            </div>
          )}
        </div>
      </div>
    </>
  );
}
