"""Classe base per parser di documenti bancari.

Ogni parser (PDF, LLM, CSV) deve estendere DocumentParser e implementare:
- parse(): estrazione dati dal documento
- cross_validate(): verifica coerenza interna dei dati estratti

Il sistema di confidence scoring (0.0–1.0) indica l'affidabilità dell'estrazione.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Any


class ConfidenceLevel(Enum):
    """Livelli di confidenza per estrazione dati."""

    HIGH = "high"        # > 0.90 — Dati verificati, coerenti
    MEDIUM = "medium"    # 0.70–0.90 — Dati probabilmente corretti
    LOW = "low"          # 0.50–0.70 — Richiede revisione manuale
    VERY_LOW = "very_low"  # < 0.50 — Estrazione incerta


@dataclass
class ExtractedField:
    """Singolo campo estratto con metadati di confidenza.

    Attributes:
        name: nome del campo (es. "isin", "quantity")
        value: valore estratto
        confidence: score 0.0–1.0
        source: da dove è stato estratto (es. "page_1_table_2")
        raw_text: testo grezzo originale
    """

    name: str
    value: Any
    confidence: float = 1.0
    source: str = ""
    raw_text: str = ""


@dataclass
class ValidationWarning:
    """Avviso di validazione durante cross_validate.

    Attributes:
        field: campo coinvolto
        message: descrizione del problema
        severity: gravità (info, warning, error)
        expected: valore atteso (se disponibile)
        actual: valore trovato
    """

    field: str
    message: str
    severity: str = "warning"  # info, warning, error
    expected: str = ""
    actual: str = ""


@dataclass
class ParseResult:
    """Risultato dell'estrazione dati da un documento.

    Attributes:
        fields: dizionario campi estratti
        overall_confidence: confidenza complessiva (media pesata)
        warnings: lista avvisi di validazione
        raw_text: testo completo estratto dal documento
        metadata: metadati aggiuntivi (pagine, formato, etc.)
    """

    fields: dict[str, ExtractedField] = field(default_factory=dict)
    overall_confidence: float = 0.0
    warnings: list[ValidationWarning] = field(default_factory=list)
    raw_text: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_value(self, field_name: str, default: Any = None) -> Any:
        """Recupera il valore di un campo estratto."""
        f = self.fields.get(field_name)
        return f.value if f is not None else default

    def get_confidence(self, field_name: str) -> float:
        """Recupera la confidenza di un campo."""
        f = self.fields.get(field_name)
        return f.confidence if f is not None else 0.0

    def to_dict(self) -> dict:
        """Converte in dizionario per serializzazione."""
        return {
            "fields": {
                k: {"value": v.value, "confidence": v.confidence, "source": v.source}
                for k, v in self.fields.items()
            },
            "overall_confidence": self.overall_confidence,
            "warnings": [
                {"field": w.field, "message": w.message, "severity": w.severity}
                for w in self.warnings
            ],
        }

    @property
    def confidence_level(self) -> ConfidenceLevel:
        """Determina il livello di confidenza complessivo."""
        if self.overall_confidence > 0.90:
            return ConfidenceLevel.HIGH
        if self.overall_confidence > 0.70:
            return ConfidenceLevel.MEDIUM
        if self.overall_confidence > 0.50:
            return ConfidenceLevel.LOW
        return ConfidenceLevel.VERY_LOW


# Campi standard attesi per un fissato bollato
FISSATO_BOLLATO_FIELDS = [
    "isin", "security_name", "transaction_type", "trade_date",
    "settlement_date", "quantity", "unit_price", "gross_amount",
    "accrued_interest", "bank_commission", "stamp_duty",
    "tobin_tax", "total_costs", "net_settlement_amount",
]


class DocumentParser(ABC):
    """Classe base astratta per parser documenti bancari.

    Ogni implementazione deve:
    1. Estrarre i dati dal documento (parse)
    2. Verificare la coerenza interna (cross_validate)
    3. Restituire un ParseResult con confidence scoring
    """

    @abstractmethod
    def parse(self, content: bytes, filename: str = "") -> ParseResult:
        """Estrae dati dal contenuto del documento.

        Args:
            content: contenuto binario del file
            filename: nome file originale (per identificare formato)

        Returns:
            ParseResult con campi estratti e confidenza.
        """
        ...

    def cross_validate(self, result: ParseResult) -> ParseResult:
        """Verifica coerenza interna dei dati estratti.

        Controlli standard:
        1. tel_quel = gross_amount + accrued_interest
        2. net_settlement = tel_quel + total_costs
        3. total_costs = commission + stamp_duty + tobin_tax + other
        4. quantity > 0, unit_price > 0
        5. settlement_date >= trade_date

        Args:
            result: risultato dell'estrazione

        Returns:
            ParseResult aggiornato con eventuali warning.
        """
        warnings: list[ValidationWarning] = []

        gross = result.get_value("gross_amount")
        accrued = result.get_value("accrued_interest", Decimal("0"))
        tel_quel = result.get_value("tel_quel_amount")
        net = result.get_value("net_settlement_amount")
        total_costs = result.get_value("total_costs", Decimal("0"))

        # Check 1: tel_quel = gross + accrued
        if gross is not None and tel_quel is not None and accrued is not None:
            expected_tq = gross + accrued
            if abs(expected_tq - tel_quel) > Decimal("0.02"):
                warnings.append(ValidationWarning(
                    field="tel_quel_amount",
                    message="tel_quel ≠ gross_amount + accrued_interest",
                    severity="error",
                    expected=str(expected_tq),
                    actual=str(tel_quel),
                ))

        # Check 2: net = tel_quel + costs
        if tel_quel is not None and net is not None and total_costs is not None:
            expected_net = tel_quel + total_costs
            if abs(expected_net - net) > Decimal("0.02"):
                warnings.append(ValidationWarning(
                    field="net_settlement_amount",
                    message="net_settlement ≠ tel_quel + total_costs",
                    severity="error",
                    expected=str(expected_net),
                    actual=str(net),
                ))

        # Check 3: quantity > 0
        qty = result.get_value("quantity")
        if qty is not None and qty <= 0:
            warnings.append(ValidationWarning(
                field="quantity",
                message="La quantità deve essere positiva",
                severity="error",
                actual=str(qty),
            ))

        # Check 4: settlement >= trade
        trade = result.get_value("trade_date")
        settle = result.get_value("settlement_date")
        if trade is not None and settle is not None and settle < trade:
            warnings.append(ValidationWarning(
                field="settlement_date",
                message="Data regolamento precedente a data operazione",
                severity="error",
                expected=f">= {trade}",
                actual=str(settle),
            ))

        result.warnings.extend(warnings)

        # Aggiorna confidenza: abbassa per ogni errore
        error_count = sum(1 for w in warnings if w.severity == "error")
        if error_count > 0:
            penalty = min(error_count * 0.15, 0.50)
            result.overall_confidence = max(0.0, result.overall_confidence - penalty)

        return result

    def _compute_overall_confidence(self, result: ParseResult) -> float:
        """Calcola confidenza complessiva come media pesata dei campi.

        Campi critici (ISIN, quantity, amount) pesano di più.
        """
        if not result.fields:
            return 0.0

        # Pesi per campo: campi critici hanno peso maggiore
        weights = {
            "isin": 2.0,
            "quantity": 2.0,
            "unit_price": 1.5,
            "gross_amount": 2.0,
            "net_settlement_amount": 2.0,
            "trade_date": 1.5,
            "settlement_date": 1.0,
            "accrued_interest": 1.0,
            "bank_commission": 0.8,
        }

        total_weight = 0.0
        weighted_sum = 0.0

        for name, f in result.fields.items():
            w = weights.get(name, 1.0)
            total_weight += w
            weighted_sum += f.confidence * w

        return weighted_sum / total_weight if total_weight > 0 else 0.0
