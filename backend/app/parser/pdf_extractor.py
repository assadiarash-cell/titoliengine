"""Estrazione testo e tabelle da PDF con pdfplumber, fallback pymupdf.

Supporta fissati bollato, cedolini, estratti conto delle principali banche italiane.
"""
import logging
import re
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

# Regex per campi comuni nei documenti bancari italiani
ISIN_RE = re.compile(r"\b([A-Z]{2}[A-Z0-9]{9}\d)\b")
DATE_RE = re.compile(r"\b(\d{2}[/.-]\d{2}[/.-]\d{4})\b")
AMOUNT_RE = re.compile(r"[\d]{1,3}(?:[.\s]\d{3})*,\d{2}")


def _parse_italian_date(text: str) -> date | None:
    """Parsa una data in formato italiano (dd/mm/yyyy)."""
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(text.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _parse_italian_amount(text: str) -> Decimal | None:
    """Parsa un importo in formato italiano (1.234,56 → 1234.56)."""
    try:
        cleaned = text.strip().replace(".", "").replace(",", ".")
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None


class PDFExtractor(DocumentParser):
    """Estrae dati da PDF bancari usando pdfplumber con fallback pymupdf.

    Strategia:
    1. Tenta estrazione con pdfplumber (migliore per tabelle)
    2. Se fallisce, usa pymupdf (fitz) per testo puro
    3. Applica regex per identificare campi strutturati
    """

    def parse(self, content: bytes, filename: str = "") -> ParseResult:
        """Estrae dati da un PDF.

        Args:
            content: contenuto binario del PDF
            filename: nome file originale

        Returns:
            ParseResult con campi estratti e confidenza.
        """
        result = ParseResult(metadata={"filename": filename})

        # Tenta pdfplumber
        text = self._extract_with_pdfplumber(content)
        if not text or len(text.strip()) < 50:
            # Fallback pymupdf
            text = self._extract_with_pymupdf(content)
            result.metadata["extraction_method"] = "pymupdf"
        else:
            result.metadata["extraction_method"] = "pdfplumber"

        if not text or len(text.strip()) < 20:
            result.overall_confidence = 0.0
            result.warnings.append(ValidationWarning(
                field="raw_text",
                message="Impossibile estrarre testo dal PDF",
                severity="error",
            ))
            return result

        result.raw_text = text
        self._extract_fields(text, result)
        result.overall_confidence = self._compute_overall_confidence(result)
        return self.cross_validate(result)

    def _extract_with_pdfplumber(self, content: bytes) -> str:
        """Estrae testo con pdfplumber."""
        try:
            import pdfplumber
            import io

            text_parts: list[str] = []
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    text_parts.append(page_text)

                    # Estrai anche tabelle
                    tables = page.extract_tables() or []
                    for table in tables:
                        for row in table:
                            if row:
                                text_parts.append(
                                    " | ".join(str(c) for c in row if c)
                                )

            return "\n".join(text_parts)
        except Exception as e:
            logger.warning("pdfplumber extraction failed: %s", e)
            return ""

    def _extract_with_pymupdf(self, content: bytes) -> str:
        """Fallback: estrae testo con pymupdf (fitz)."""
        try:
            import fitz  # pymupdf

            doc = fitz.open(stream=content, filetype="pdf")
            text_parts = [page.get_text() for page in doc]
            doc.close()
            return "\n".join(text_parts)
        except Exception as e:
            logger.warning("pymupdf extraction failed: %s", e)
            return ""

    def _extract_fields(self, text: str, result: ParseResult) -> None:
        """Estrae campi strutturati dal testo con regex."""
        text_upper = text.upper()

        # ISIN
        isin_matches = ISIN_RE.findall(text)
        if isin_matches:
            result.fields["isin"] = ExtractedField(
                name="isin",
                value=isin_matches[0],
                confidence=0.95,
                source="regex",
                raw_text=isin_matches[0],
            )

        # Date
        date_matches = DATE_RE.findall(text)
        dates = [_parse_italian_date(d) for d in date_matches]
        dates = [d for d in dates if d is not None]

        if len(dates) >= 1:
            result.fields["trade_date"] = ExtractedField(
                name="trade_date",
                value=dates[0],
                confidence=0.80,
                source="regex_first_date",
            )
        if len(dates) >= 2:
            result.fields["settlement_date"] = ExtractedField(
                name="settlement_date",
                value=dates[1],
                confidence=0.75,
                source="regex_second_date",
            )

        # Tipo operazione
        if any(k in text_upper for k in ("ACQUISTO", "COMPRA", "BUY")):
            result.fields["transaction_type"] = ExtractedField(
                name="transaction_type",
                value="purchase",
                confidence=0.90,
                source="keyword_match",
            )
        elif any(k in text_upper for k in ("VENDITA", "VENDI", "SELL")):
            result.fields["transaction_type"] = ExtractedField(
                name="transaction_type",
                value="sale",
                confidence=0.90,
                source="keyword_match",
            )
        elif any(k in text_upper for k in ("CEDOLA", "COUPON", "STACCO")):
            result.fields["transaction_type"] = ExtractedField(
                name="transaction_type",
                value="coupon_receipt",
                confidence=0.90,
                source="keyword_match",
            )

        # Importi — cerca tutti gli importi nel testo
        amounts = AMOUNT_RE.findall(text)
        parsed_amounts = [_parse_italian_amount(a) for a in amounts]
        parsed_amounts = [a for a in parsed_amounts if a is not None and a > 0]

        if parsed_amounts:
            # L'importo più grande è probabilmente il net_settlement
            sorted_amounts = sorted(parsed_amounts, reverse=True)

            if len(sorted_amounts) >= 1:
                result.fields["net_settlement_amount"] = ExtractedField(
                    name="net_settlement_amount",
                    value=sorted_amounts[0],
                    confidence=0.65,
                    source="largest_amount",
                )

            # Cerca importi associati a label specifiche
            self._extract_labeled_amounts(text, result)

        # Quantità — cerca pattern tipici
        qty_patterns = [
            r"(?:quantit[àa]|nominale|nom\.?)\s*[:=]?\s*([\d.]+(?:,\d+)?)",
            r"([\d.]+(?:,\d+)?)\s*(?:nominale|nom\.)",
        ]
        for pattern in qty_patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                qty = _parse_italian_amount(m.group(1))
                if qty and qty > 0:
                    result.fields["quantity"] = ExtractedField(
                        name="quantity",
                        value=qty,
                        confidence=0.75,
                        source="regex_labeled",
                        raw_text=m.group(0),
                    )
                    break

    def _extract_labeled_amounts(self, text: str, result: ParseResult) -> None:
        """Estrae importi associati a etichette specifiche."""
        labels = {
            "gross_amount": [
                r"(?:controvalore|importo)\s*[:=]?\s*([\d.]+,\d{2})",
                r"(?:corso secco|clean)\s*[:=]?\s*([\d.]+,\d{2})",
            ],
            "accrued_interest": [
                r"(?:rateo|dietimo|accrued)\s*[:=]?\s*([\d.]+,\d{2})",
            ],
            "bank_commission": [
                r"(?:commissioni?|commission)\s*[:=]?\s*([\d.]+,\d{2})",
            ],
            "stamp_duty": [
                r"(?:bollo|imposta|stamp)\s*[:=]?\s*([\d.]+,\d{2})",
            ],
            "unit_price": [
                r"(?:prezzo|corso|price)\s*[:=]?\s*([\d.]+,\d{2,4})",
            ],
        }

        for field_name, patterns in labels.items():
            for pattern in patterns:
                m = re.search(pattern, text, re.IGNORECASE)
                if m:
                    val = _parse_italian_amount(m.group(1))
                    if val is not None:
                        result.fields[field_name] = ExtractedField(
                            name=field_name,
                            value=val,
                            confidence=0.80,
                            source="regex_labeled",
                            raw_text=m.group(0),
                        )
                        break
