"""Estrazione AI-assisted di dati da documenti bancari con Anthropic API.

IMPORTANTE: Il LLM è usato SOLO per estrazione dati strutturati, MAI per calcoli contabili.
Tutti i calcoli contabili sono deterministici e gestiti dal motore (app.engine).

Il prompt strutturato chiede di estrarre:
- ISIN, quantità, prezzo, rateo, commissioni, bolli
- Data operazione, tipo operazione
- Output validato con confidence score
"""
import json
import logging
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from .base import (
    DocumentParser,
    ExtractedField,
    ParseResult,
    ValidationWarning,
)

logger = logging.getLogger(__name__)

# Prompt strutturato per Anthropic Claude
EXTRACTION_PROMPT = """Sei un assistente specializzato nell'analisi di documenti bancari italiani (fissati bollato, cedolini, estratti conto).

Analizza il seguente testo estratto da un documento PDF e identifica i campi elencati.
Per ogni campo trovato, indica anche un livello di confidenza (0.0 = non trovato, 1.0 = certissimo).

CAMPI DA ESTRARRE:
1. isin — Codice ISIN del titolo (es. IT0005580094)
2. security_name — Nome del titolo (es. "BTP 3.5% 01/03/2030")
3. transaction_type — Tipo operazione: "purchase", "sale", "coupon_receipt", "maturity_redemption"
4. trade_date — Data operazione (formato YYYY-MM-DD)
5. settlement_date — Data regolamento (formato YYYY-MM-DD)
6. quantity — Quantità/Nominale
7. unit_price — Prezzo unitario (corso secco)
8. gross_amount — Controvalore lordo (corso secco × quantità / 100)
9. accrued_interest — Rateo/Dietimo cedolare
10. tel_quel_amount — Importo tel quel (lordo + rateo)
11. bank_commission — Commissioni bancarie
12. stamp_duty — Imposta di bollo
13. tobin_tax — Tobin Tax (se presente)
14. other_costs — Altri oneri
15. total_costs — Totale oneri e commissioni
16. net_settlement_amount — Importo netto regolamento (movimento in c/c)

REGOLE:
- Tutti gli importi devono essere numeri decimali (es. 101200.00, non "101.200,00")
- Le date devono essere in formato YYYY-MM-DD
- Se un campo non è presente nel documento, omettilo dal risultato
- NON inventare dati: se non sei sicuro, abbassa la confidenza

Rispondi SOLO con un JSON valido nel seguente formato:
{
  "fields": {
    "isin": {"value": "IT0005580094", "confidence": 0.95},
    "quantity": {"value": 100000, "confidence": 0.90},
    ...
  }
}

TESTO DEL DOCUMENTO:
"""


class LLMExtractor(DocumentParser):
    """Estrazione dati da documenti usando Anthropic Claude API.

    USATO SOLO PER ESTRAZIONE DATI, MAI PER CALCOLI CONTABILI.

    Attributes:
        api_key: Anthropic API key
        model: modello Claude da usare
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-sonnet-4-20250514",
    ):
        """Inizializza l'estrattore LLM.

        Args:
            api_key: Anthropic API key. Se None, legge da settings.
            model: ID modello Claude.
        """
        self.api_key = api_key
        self.model = model

    def parse(self, content: bytes, filename: str = "") -> ParseResult:
        """Estrae dati usando il LLM come parser intelligente.

        Il testo viene prima estratto dal PDF con il PDFExtractor,
        poi inviato al LLM per parsing strutturato.

        Args:
            content: contenuto binario del file
            filename: nome file originale

        Returns:
            ParseResult con campi estratti e confidenza.
        """
        from .pdf_extractor import PDFExtractor

        # Step 1: estrai testo grezzo dal PDF
        pdf_extractor = PDFExtractor()
        raw_result = pdf_extractor.parse(content, filename)
        raw_text = raw_result.raw_text

        if not raw_text or len(raw_text.strip()) < 20:
            return ParseResult(
                overall_confidence=0.0,
                warnings=[ValidationWarning(
                    field="raw_text",
                    message="Nessun testo estratto dal PDF per il LLM",
                    severity="error",
                )],
            )

        # Step 2: chiama il LLM per parsing strutturato
        llm_response = self._call_anthropic(raw_text)

        if llm_response is None:
            # Fallback: usa solo i dati estratti dal PDF
            return raw_result

        # Step 3: costruisci il ParseResult dal JSON del LLM
        result = self._build_result(llm_response, raw_text, filename)

        # Step 4: cross-validate
        result = self.cross_validate(result)
        return result

    def _call_anthropic(self, text: str) -> dict | None:
        """Chiama Anthropic API per estrazione strutturata.

        Returns:
            Dict con i campi estratti o None se fallisce.
        """
        api_key = self.api_key
        if not api_key:
            try:
                from app.config import settings
                api_key = getattr(settings, "anthropic_api_key", None)
            except Exception:
                pass

        if not api_key:
            logger.warning("Anthropic API key non configurata, skip LLM extraction")
            return None

        try:
            import anthropic

            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": EXTRACTION_PROMPT + text[:8000],  # Limita per tokens
                }],
            )

            # Estrai JSON dalla risposta
            response_text = message.content[0].text
            # Cerca il JSON nella risposta
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response_text[json_start:json_end])

        except ImportError:
            logger.warning("anthropic package non installato")
        except Exception as e:
            logger.error("Anthropic API call failed: %s", e)

        return None

    def _build_result(
        self, llm_data: dict, raw_text: str, filename: str
    ) -> ParseResult:
        """Costruisce ParseResult dalla risposta del LLM."""
        result = ParseResult(
            raw_text=raw_text,
            metadata={"filename": filename, "extraction_method": "llm_anthropic"},
        )

        fields_data = llm_data.get("fields", {})

        for field_name, field_info in fields_data.items():
            if not isinstance(field_info, dict):
                continue

            raw_value = field_info.get("value")
            confidence = float(field_info.get("confidence", 0.5))

            # Converti tipi
            value = self._convert_value(field_name, raw_value)
            if value is not None:
                result.fields[field_name] = ExtractedField(
                    name=field_name,
                    value=value,
                    confidence=confidence,
                    source="llm_anthropic",
                )

        result.overall_confidence = self._compute_overall_confidence(result)
        return result

    def _convert_value(self, field_name: str, raw_value: Any) -> Any:
        """Converte il valore grezzo nel tipo appropriato."""
        if raw_value is None:
            return None

        # Campi data
        if field_name in ("trade_date", "settlement_date"):
            if isinstance(raw_value, str):
                try:
                    return datetime.strptime(raw_value, "%Y-%m-%d").date()
                except ValueError:
                    return None
            return None

        # Campi numerici (importi e quantità)
        numeric_fields = {
            "quantity", "unit_price", "gross_amount", "accrued_interest",
            "tel_quel_amount", "bank_commission", "stamp_duty", "tobin_tax",
            "other_costs", "total_costs", "net_settlement_amount",
        }
        if field_name in numeric_fields:
            try:
                return Decimal(str(raw_value))
            except (InvalidOperation, ValueError):
                return None

        # Campi stringa
        return str(raw_value)
