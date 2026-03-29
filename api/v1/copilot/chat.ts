/**
 * Vercel Edge Function — Copilot Chat proxy to Claude API.
 * No Python, no DB, no size limit issues.
 * Streams SSE responses directly from Anthropic.
 */

export const config = { runtime: 'edge' };

const SYSTEM_PROMPT = `Sei il Copilot di TitoliEngine — un assistente AI integrato nel motore contabile per titoli di debito (OIC 20).

Puoi aiutare l'utente con:
- Spiegare concetti OIC 20: costo ammortizzato, TIR, ratei, scarti di negoziazione, svalutazioni, ripristini
- Guidare nell'uso dell'applicazione: come creare operazioni, approvare scritture, generare report
- Spiegare il flusso contabile: acquisto → scrittura → valutazione → report
- Rispondere a domande su normativa italiana titoli di debito
- Analisi e suggerimenti su portafoglio e operazioni

NOTA: Al momento il backend dati non è connesso in produzione. Se l'utente chiede dati specifici (portafoglio, operazioni, etc.), spiega che i dati saranno disponibili quando il backend sarà collegato, ma offri comunque spiegazioni e guida.

Rispondi SEMPRE in italiano. Sii conciso e professionale.
Per importi usa formato italiano (es. 1.234,56 €).
Data odierna: ${new Date().toISOString().split('T')[0]}`;

export default async function handler(req: Request): Promise<Response> {
  if (req.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method not allowed' }), { status: 405 });
  }

  const apiKey = process.env.TE_ANTHROPIC_API_KEY;
  if (!apiKey) {
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(new TextEncoder().encode(
          `data: ${JSON.stringify({ type: 'error', content: 'API key Anthropic non configurata sul server.' })}\n\n`
        ));
        controller.close();
      }
    });
    return new Response(stream, {
      headers: { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache' },
    });
  }

  let body: { messages: { role: string; content: string }[]; context?: { page?: string } };
  try {
    body = await req.json();
  } catch {
    return new Response(JSON.stringify({ error: 'Invalid JSON' }), { status: 400 });
  }

  const messages = body.messages.map((m: { role: string; content: string }) => ({
    role: m.role,
    content: m.content,
  }));

  let system = SYSTEM_PROMPT;
  if (body.context?.page) {
    system += `\n\nL'utente si trova nella pagina: ${body.context.page}`;
  }

  try {
    const anthropicRes = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 4096,
        system,
        messages,
        stream: true,
      }),
    });

    if (!anthropicRes.ok) {
      const errText = await anthropicRes.text();
      const stream = new ReadableStream({
        start(controller) {
          controller.enqueue(new TextEncoder().encode(
            `data: ${JSON.stringify({ type: 'error', content: `Errore API Claude: ${anthropicRes.status}` })}\n\n`
          ));
          controller.close();
        }
      });
      return new Response(stream, {
        headers: { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache' },
      });
    }

    // Transform Anthropic SSE stream to our simpler format
    const encoder = new TextEncoder();
    const decoder = new TextDecoder();
    const reader = anthropicRes.body!.getReader();

    const stream = new ReadableStream({
      async start(controller) {
        let buffer = '';
        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
              if (!line.startsWith('data: ')) continue;
              const data = line.slice(6).trim();
              if (data === '[DONE]') continue;

              try {
                const event = JSON.parse(data);

                if (event.type === 'content_block_delta' && event.delta?.type === 'text_delta') {
                  controller.enqueue(encoder.encode(
                    `data: ${JSON.stringify({ type: 'text', content: event.delta.text })}\n\n`
                  ));
                } else if (event.type === 'message_stop') {
                  controller.enqueue(encoder.encode(
                    `data: ${JSON.stringify({ type: 'done' })}\n\n`
                  ));
                }
              } catch {
                // skip malformed events
              }
            }
          }
          // Ensure done event is sent
          controller.enqueue(encoder.encode(
            `data: ${JSON.stringify({ type: 'done' })}\n\n`
          ));
        } catch (err) {
          controller.enqueue(encoder.encode(
            `data: ${JSON.stringify({ type: 'error', content: 'Stream interrotto' })}\n\n`
          ));
        } finally {
          controller.close();
        }
      }
    });

    return new Response(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });
  } catch (err) {
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(new TextEncoder().encode(
          `data: ${JSON.stringify({ type: 'error', content: 'Errore di connessione con Claude API' })}\n\n`
        ));
        controller.close();
      }
    });
    return new Response(stream, {
      headers: { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache' },
    });
  }
}
