# TitoliEngine -- Guida per aggiungere un nuovo Bank Parser

Questa guida spiega come implementare un parser per estrarre dati da fissati bollati (conferme d'ordine) di una nuova banca.

---

## Indice

1. [Architettura del sistema di parsing](#1-architettura-del-sistema-di-parsing)
2. [Parser esistenti](#2-parser-esistenti)
3. [Struttura di un parser](#3-struttura-di-un-parser)
4. [Step-by-step: creare un nuovo parser](#4-step-by-step-creare-un-nuovo-parser)
5. [Campi da estrarre](#5-campi-da-estrarre)
6. [Sistema di confidence scoring](#6-sistema-di-confidence-scoring)
7. [Cross-validation](#7-cross-validation)
8. [Riconciliazione](#8-riconciliazione)
9. [LLM extractor come fallback](#9-llm-extractor-come-fallback)
10. [Testing](#10-testing)

---

## 1. Architettura del sistema di parsing

Il sistema di parsing e' organizzato in livelli:

```
Document Upload
      |
      v
+------------------+
| pdf_extractor.py |  Estrazione testo grezzo dal PDF (pdfplumber)
+--------+---------+
         |
         v
+------------------+
| Bank Parser      |  Parser specifico per banca (regex + pattern matching)
| (intesa.py, ...) |
+--------+---------+
         |         \
         |          +------------------+
         |          | llm_extractor.py |  Fallback: estrazione con LLM (Anthropic Claude)
         |          +------------------+
         v
+------------------+
| base.py          |  Cross-validation: coerenza interna dei dati estratti
| cross_validate() |
+--------+---------+
         |
         v
+------------------+
| reconciler.py    |  Riconciliazione: confronto con transazione e estratto conto
+------------------+
```

### File principali

| File | Ruolo |
|------|-------|
| `parser/base.py` | Classe astratta `DocumentParser`, dataclass `ParseResult`, `ExtractedField`, costanti |
| `parser/pdf_extractor.py` | Estrazione testo grezzo da PDF con `pdfplumber` |
| `parser/llm_extractor.py` | Estrazione dati tramite LLM (Anthropic Claude) come fallback |
| `parser/reconciler.py` | `TransactionReconciler`: riconciliazione documento vs transazione vs estratto conto |
| `parser/csv_importer.py` | Import dati da CSV bancari |
| `parser/banks/*.py` | Parser specifici per ogni banca |

---

## 2. Parser esistenti

I parser sono nella directory `backend/app/parser/banks/`:

| File | Banca | Note |
|------|-------|------|
| `intesa.py` | Intesa Sanpaolo | Fissati bollati e conferme online |
| `unicredit.py` | UniCredit | Fissati bollati e conferme |
| `fineco.py` | FinecoBank | Conferme digitali |
| `bper.py` | BPER Banca | Fissati bollati |
| `mediolanum.py` | Banca Mediolanum | Conferme operazioni |
| `banca_sella.py` | Banca Sella | Fissati bollati |
| `bpm.py` | Banco BPM | Fissati bollati |
| `generic.py` | Parser generico | Fallback per banche non supportate |

Il parser `generic.py` usa pattern regex generali e ha confidence piu' bassa. E' il fallback quando non esiste un parser specifico.

---

## 3. Struttura di un parser

Ogni parser e' una classe che estende `DocumentParser` da `parser/base.py`.

### Classe base `DocumentParser`

```python
class DocumentParser(ABC):

    @abstractmethod
    def parse(self, content: bytes, filename: str = "") -> ParseResult:
        """Estrae dati dal contenuto del documento."""
        ...

    def cross_validate(self, result: ParseResult) -> ParseResult:
        """Verifica coerenza interna (gia' implementato nella base)."""
        ...

    def _compute_overall_confidence(self, result: ParseResult) -> float:
        """Calcola confidenza media pesata."""
        ...
```

### Dataclass principali

**`ExtractedField`** -- Singolo campo estratto:

| Attributo | Tipo | Descrizione |
|-----------|------|-------------|
| `name` | `str` | Nome del campo (es. `"isin"`, `"quantity"`) |
| `value` | `Any` | Valore estratto |
| `confidence` | `float` | Score 0.0-1.0 |
| `source` | `str` | Provenienza (es. `"page_1_table_2"`) |
| `raw_text` | `str` | Testo grezzo originale |

**`ParseResult`** -- Risultato completo:

| Attributo | Tipo | Descrizione |
|-----------|------|-------------|
| `fields` | `dict[str, ExtractedField]` | Campi estratti |
| `overall_confidence` | `float` | Confidenza complessiva 0.0-1.0 |
| `warnings` | `list[ValidationWarning]` | Avvisi di validazione |
| `raw_text` | `str` | Testo completo estratto |
| `metadata` | `dict` | Metadati (pagine, formato, etc.) |

---

## 4. Step-by-step: creare un nuovo parser

### Passo 1: Raccogliere campioni

Raccogliere almeno 5-10 fissati bollati della banca target. Analizzare:
- Layout del documento (tabelle, campi liberi)
- Posizione dei dati chiave (ISIN, importi, date)
- Formati numerici (es. `1.234,56` vs `1,234.56`)
- Formati date (es. `DD/MM/YYYY` vs `DD-MM-YYYY`)
- Varianti per tipo di operazione (acquisto, vendita, rimborso)

### Passo 2: Creare il file del parser

Creare `backend/app/parser/banks/nuova_banca.py`:

```python
"""Parser per fissati bollati di NuovaBanca."""
import re
from datetime import date, datetime
from decimal import Decimal

from app.parser.base import (
    DocumentParser,
    ExtractedField,
    ParseResult,
    ValidationWarning,
)
from app.parser.pdf_extractor import extract_text_from_pdf


class NuovaBancaParser(DocumentParser):
    """Parser specifico per NuovaBanca.

    Supporta:
    - Fissati bollati acquisto/vendita titoli di debito
    - Conferme incasso cedola
    - Conferme rimborso a scadenza
    """

    # Pattern regex specifici per NuovaBanca
    ISIN_PATTERN = re.compile(r"ISIN[:\s]+([A-Z]{2}[A-Z0-9]{10})")
    QUANTITY_PATTERN = re.compile(r"Quantit[aà]\s*[:\s]+([\d.,]+)")
    PRICE_PATTERN = re.compile(r"Prezzo\s*[:\s]+([\d.,]+)")
    DATE_PATTERN = re.compile(r"(\d{2}/\d{2}/\d{4})")

    # Aggiungere tutti i pattern necessari...

    def parse(self, content: bytes, filename: str = "") -> ParseResult:
        """Estrae dati dal fissato bollato NuovaBanca."""
        result = ParseResult()

        # 1. Estrai testo dal PDF
        raw_text = extract_text_from_pdf(content)
        result.raw_text = raw_text

        # 2. Estrai ogni campo
        result.fields["isin"] = self._extract_isin(raw_text)
        result.fields["quantity"] = self._extract_quantity(raw_text)
        result.fields["unit_price"] = self._extract_price(raw_text)
        result.fields["trade_date"] = self._extract_trade_date(raw_text)
        result.fields["settlement_date"] = self._extract_settlement_date(raw_text)
        result.fields["gross_amount"] = self._extract_gross_amount(raw_text)
        result.fields["accrued_interest"] = self._extract_accrued_interest(raw_text)
        result.fields["bank_commission"] = self._extract_commission(raw_text)
        result.fields["stamp_duty"] = self._extract_stamp_duty(raw_text)
        result.fields["net_settlement_amount"] = self._extract_net_amount(raw_text)
        result.fields["transaction_type"] = self._extract_type(raw_text)
        result.fields["security_name"] = self._extract_security_name(raw_text)

        # 3. Rimuovi campi non trovati
        result.fields = {
            k: v for k, v in result.fields.items()
            if v is not None and v.value is not None
        }

        # 4. Calcola confidenza complessiva
        result.overall_confidence = self._compute_overall_confidence(result)

        # 5. Cross-validation (metodo della classe base)
        result = self.cross_validate(result)

        return result

    def _extract_isin(self, text: str) -> ExtractedField | None:
        """Estrae il codice ISIN."""
        match = self.ISIN_PATTERN.search(text)
        if match:
            return ExtractedField(
                name="isin",
                value=match.group(1),
                confidence=0.95,
                source="regex_match",
                raw_text=match.group(0),
            )
        return None

    def _extract_quantity(self, text: str) -> ExtractedField | None:
        """Estrae la quantita'/nominale."""
        match = self.QUANTITY_PATTERN.search(text)
        if match:
            raw = match.group(1)
            value = self._parse_italian_number(raw)
            return ExtractedField(
                name="quantity",
                value=value,
                confidence=0.90,
                source="regex_match",
                raw_text=raw,
            )
        return None

    # Implementare tutti gli altri _extract_* ...

    @staticmethod
    def _parse_italian_number(text: str) -> Decimal:
        """Converte numero in formato italiano (1.234,56) in Decimal."""
        cleaned = text.replace(".", "").replace(",", ".")
        return Decimal(cleaned)

    @staticmethod
    def _parse_italian_date(text: str) -> date:
        """Converte data in formato DD/MM/YYYY."""
        return datetime.strptime(text, "%d/%m/%Y").date()
```

### Passo 3: Registrare nel factory

Aggiornare `backend/app/parser/banks/__init__.py` per registrare il nuovo parser:

```python
from .nuova_banca import NuovaBancaParser

# Nel dizionario dei parser registrati
BANK_PARSERS = {
    "intesa": IntesaParser,
    "unicredit": UniCreditParser,
    "fineco": FinecoParser,
    "bper": BPERParser,
    "mediolanum": MediolanumParser,
    "banca_sella": BancaSellaParser,
    "bpm": BPMParser,
    "nuova_banca": NuovaBancaParser,  # <-- Aggiungere qui
    "generic": GenericParser,  # Sempre ultimo: fallback
}
```

### Passo 4: Testare

Vedi sezione [Testing](#10-testing).

---

## 5. Campi da estrarre

Ogni parser deve cercare di estrarre questi campi standard definiti in `FISSATO_BOLLATO_FIELDS`:

| Campo | Tipo | Obbligatorio | Descrizione |
|-------|------|:------------:|-------------|
| `isin` | `str` | Si | Codice ISIN a 12 caratteri |
| `security_name` | `str` | No | Denominazione del titolo |
| `transaction_type` | `str` | Si | `purchase`, `sale`, `coupon`, `maturity` |
| `trade_date` | `date` | Si | Data esecuzione operazione |
| `settlement_date` | `date` | Si | Data regolamento/valuta |
| `quantity` | `Decimal` | Si | Quantita' nominale |
| `unit_price` | `Decimal` | Si | Prezzo unitario (per 100 nominale) |
| `gross_amount` | `Decimal` | Si | Controvalore lordo (corso secco) |
| `accrued_interest` | `Decimal` | No | Rateo cedolare maturato |
| `bank_commission` | `Decimal` | No | Commissioni bancarie |
| `stamp_duty` | `Decimal` | No | Imposta di bollo |
| `tobin_tax` | `Decimal` | No | Tobin tax (se applicabile) |
| `total_costs` | `Decimal` | No | Totale oneri accessori |
| `net_settlement_amount` | `Decimal` | Si | Importo netto da regolare |

### Relazioni tra campi

Queste relazioni sono verificate dalla cross-validation:

```
tel_quel_amount    = gross_amount + accrued_interest
total_costs        = bank_commission + stamp_duty + tobin_tax + other
net_settlement     = tel_quel_amount + total_costs  (acquisto)
net_settlement     = tel_quel_amount - total_costs  (vendita)
gross_amount       = quantity * unit_price / 100     (per titoli quotati per 100)
```

---

## 6. Sistema di confidence scoring

Ogni campo estratto ha un punteggio di confidenza tra 0.0 e 1.0:

| Livello | Range | Significato |
|---------|-------|-------------|
| `HIGH` | > 0.90 | Dati verificati, coerenti |
| `MEDIUM` | 0.70 - 0.90 | Dati probabilmente corretti |
| `LOW` | 0.50 - 0.70 | Richiede revisione manuale |
| `VERY_LOW` | < 0.50 | Estrazione incerta |

### Come assegnare la confidenza

**Confidenza alta (0.90-1.00):**
- Campo trovato con pattern specifico della banca
- Formato riconosciuto con certezza (ISIN validato, data parsata)
- Campo in posizione attesa nel layout

**Confidenza media (0.70-0.89):**
- Campo trovato con pattern generico
- Formato leggermente diverso dall'atteso
- Posizione insolita nel documento

**Confidenza bassa (0.50-0.69):**
- Campo estratto per inferenza (calcolato da altri campi)
- Formato ambiguo (es. numero senza contesto)
- Fallback LLM

### Calcolo confidenza complessiva

La confidenza complessiva (`overall_confidence`) e' una media pesata dei campi. I campi critici hanno peso maggiore:

| Campo | Peso |
|-------|------|
| `isin` | 2.0 |
| `quantity` | 2.0 |
| `gross_amount` | 2.0 |
| `net_settlement_amount` | 2.0 |
| `unit_price` | 1.5 |
| `trade_date` | 1.5 |
| `settlement_date` | 1.0 |
| `accrued_interest` | 1.0 |
| `bank_commission` | 0.8 |

La cross-validation riduce la confidenza di 0.15 per ogni errore di coerenza trovato (max -0.50).

---

## 7. Cross-validation

Il metodo `cross_validate()` nella classe base `DocumentParser` verifica la coerenza interna dei dati estratti. Le verifiche sono:

| # | Verifica | Severita' |
|---|----------|-----------|
| 1 | `tel_quel = gross_amount + accrued_interest` | error |
| 2 | `net_settlement = tel_quel + total_costs` | error |
| 3 | `quantity > 0` | error |
| 4 | `settlement_date >= trade_date` | error |

**Non serve reimplementare `cross_validate()`** nel parser specifico: la versione nella classe base copre tutti i controlli standard. Il parser chiama semplicemente `self.cross_validate(result)` alla fine del metodo `parse()`.

Se servono controlli aggiuntivi specifici per una banca, si puo' sovrascrivere il metodo:

```python
def cross_validate(self, result: ParseResult) -> ParseResult:
    # Esegui i controlli standard
    result = super().cross_validate(result)

    # Aggiungi controlli specifici NuovaBanca
    # ...

    return result
```

---

## 8. Riconciliazione

Dopo l'estrazione, il `TransactionReconciler` (`parser/reconciler.py`) confronta i dati estratti con la transazione nel database e (opzionalmente) con il movimento sull'estratto conto.

### Due livelli di riconciliazione

**1. Documento vs Transazione** (`reconcile_document_vs_transaction`):

Confronta i dati estratti dal PDF con quelli inseriti manualmente nella transazione. Campi confrontati:
- `net_settlement_amount`, `gross_amount`, `accrued_interest`, `bank_commission`
- `quantity`, `unit_price`
- `trade_date`, `settlement_date`
- `isin` (discrepanza ISIN = severita' CRITICAL)

**2. Transazione vs Estratto conto** (`reconcile_with_statement`):

Confronta l'importo netto della transazione con il movimento sul conto corrente.

### Severita' discrepanze

| Severita' | Soglia (diff/valore) | Significato |
|-----------|---------------------|-------------|
| `INFO` | <= 0.1% | Differenza trascurabile |
| `WARNING` | 0.1% - 1% | Richiede attenzione |
| `ERROR` | 1% - 5% | Differenza significativa |
| `CRITICAL` | > 5% o ISIN diverso | Possibile errore grave |

Tolleranza base: 0.02 EUR (2 centesimi).

---

## 9. LLM extractor come fallback

Quando il parser specifico non riesce ad estrarre tutti i campi (o la confidenza e' troppo bassa), il sistema puo' usare l'`LLMExtractor` (`parser/llm_extractor.py`) come fallback.

L'LLM extractor:
1. Invia il testo grezzo del PDF ad Anthropic Claude
2. Chiede di estrarre i campi nel formato strutturato atteso
3. Assegna confidenza `MEDIUM` (0.70-0.80) ai campi estratti dall'LLM
4. I risultati vengono comunque sottoposti a cross-validation

### Requisiti

- Variabile d'ambiente `TE_ANTHROPIC_API_KEY` configurata
- Se non disponibile, il fallback LLM viene saltato

### Quando si attiva

Il fallback LLM e' utile quando:
- Il parser specifico non esiste per quella banca
- Il parser generico ha confidenza < 0.50
- Mancano campi obbligatori dopo il parsing regex

---

## 10. Testing

### Struttura dei test

I test per i parser sono in `backend/tests/parser/`:

| File | Copertura |
|------|-----------|
| `test_pdf_extractor.py` | Estrazione testo da PDF |
| `test_reconciler.py` | Riconciliazione documento vs transazione |

### Creare test per un nuovo parser

Creare `backend/tests/parser/test_nuova_banca.py`:

```python
"""Test per NuovaBanca parser."""
from decimal import Decimal
from datetime import date

import pytest

from app.parser.banks.nuova_banca import NuovaBancaParser


class TestNuovaBancaParser:
    """Test suite per NuovaBancaParser."""

    def setup_method(self):
        self.parser = NuovaBancaParser()

    def test_parse_acquisto_btp(self):
        """Estrae correttamente un acquisto BTP."""
        # Caricare un PDF campione o usare testo mock
        with open("tests/fixtures/nuova_banca_acquisto_btp.pdf", "rb") as f:
            content = f.read()

        result = self.parser.parse(content, filename="acquisto_btp.pdf")

        # Verifica campi principali
        assert result.get_value("isin") == "IT0005560948"
        assert result.get_value("transaction_type") == "purchase"
        assert result.get_value("quantity") == Decimal("100000")
        assert result.get_value("unit_price") == Decimal("98.50")
        assert result.get_value("trade_date") == date(2025, 1, 15)
        assert result.get_value("settlement_date") == date(2025, 1, 17)

        # Verifica confidenza
        assert result.overall_confidence > 0.80
        assert result.get_confidence("isin") > 0.90

        # Nessun errore di cross-validation
        errors = [w for w in result.warnings if w.severity == "error"]
        assert len(errors) == 0

    def test_parse_vendita(self):
        """Estrae correttamente una vendita."""
        # ...

    def test_cross_validation_coerenza_importi(self):
        """Verifica che la cross-validation rilevi incoerenze."""
        # ...

    def test_formato_numeri_italiani(self):
        """Verifica parsing corretto di 1.234.567,89."""
        result = NuovaBancaParser._parse_italian_number("1.234.567,89")
        assert result == Decimal("1234567.89")

    def test_confidenza_campo_mancante(self):
        """Confidenza bassa se mancano campi critici."""
        # PDF con dati parziali
        # ...
```

### Checklist test

Per ogni nuovo parser, verificare:

- [ ] Acquisto titolo a cedola fissa (BTP, obbligazione corporate)
- [ ] Acquisto titolo zero coupon (BOT, CTZ)
- [ ] Vendita con plusvalenza
- [ ] Vendita con minusvalenza
- [ ] Incasso cedola
- [ ] Rimborso a scadenza
- [ ] Formato numeri italiani (separatore migliaia `.`, decimali `,`)
- [ ] Formato date (DD/MM/YYYY)
- [ ] ISIN estratto correttamente
- [ ] Cross-validation: importi coerenti
- [ ] Cross-validation: date coerenti
- [ ] Confidenza > 0.80 per documenti standard
- [ ] Confidenza < 0.50 per documenti corrotti/parziali
- [ ] Nessun errore su campi opzionali mancanti

### Fixture

Mettere i PDF campione in `backend/tests/fixtures/` con naming convention:

```
{banca}_{tipo_operazione}_{titolo}.pdf

Esempi:
nuova_banca_acquisto_btp.pdf
nuova_banca_vendita_corporate.pdf
nuova_banca_cedola_btp.pdf
nuova_banca_rimborso_bot.pdf
```
