"""Riconciliazione documenti bancari con transazioni registrate.

Verifica che:
1. Il totale fissato bollato corrisponda al movimento su estratto conto
2. I dati estratti siano coerenti con i dati inseriti nella transazione
3. Segnala discrepanze con flag di gravità

Riferimento: principi generali di revisione e controllo interno.
"""
import uuid
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Any

from app.engine.constants import QUANTIZE_CENTS


class DiscrepancySeverity(Enum):
    """Gravità della discrepanza rilevata."""

    INFO = "info"          # Differenza minore, informativa
    WARNING = "warning"    # Differenza significativa, richiede attenzione
    ERROR = "error"        # Differenza grave, blocca registrazione
    CRITICAL = "critical"  # Discrepanza critica, possibile errore nel documento


@dataclass
class Discrepancy:
    """Singola discrepanza rilevata durante riconciliazione.

    Attributes:
        field: campo coinvolto nella discrepanza
        expected: valore atteso (dal documento/fissato bollato)
        actual: valore trovato (dalla transazione/estratto conto)
        difference: differenza numerica (se applicabile)
        severity: gravità della discrepanza
        message: descrizione leggibile della discrepanza
    """

    field: str
    expected: str
    actual: str
    difference: Decimal | None = None
    severity: DiscrepancySeverity = DiscrepancySeverity.WARNING
    message: str = ""


@dataclass
class ReconciliationResult:
    """Risultato della riconciliazione.

    Attributes:
        is_reconciled: True se tutto quadra
        discrepancies: lista discrepanze trovate
        tolerance_used: tolleranza usata per il confronto importi (centesimi)
        document_total: totale dal documento
        transaction_total: totale dalla transazione
        statement_total: totale dall'estratto conto (se disponibile)
    """

    is_reconciled: bool = True
    discrepancies: list[Discrepancy] = field(default_factory=list)
    tolerance_used: Decimal = Decimal("0.02")
    document_total: Decimal | None = None
    transaction_total: Decimal | None = None
    statement_total: Decimal | None = None

    @property
    def has_errors(self) -> bool:
        """True se ci sono discrepanze ERROR o CRITICAL."""
        return any(
            d.severity in (DiscrepancySeverity.ERROR, DiscrepancySeverity.CRITICAL)
            for d in self.discrepancies
        )

    @property
    def has_warnings(self) -> bool:
        """True se ci sono discrepanze WARNING."""
        return any(
            d.severity == DiscrepancySeverity.WARNING
            for d in self.discrepancies
        )

    def to_dict(self) -> dict:
        """Converte in dizionario per serializzazione."""
        return {
            "is_reconciled": self.is_reconciled,
            "has_errors": self.has_errors,
            "has_warnings": self.has_warnings,
            "discrepancies": [
                {
                    "field": d.field,
                    "expected": d.expected,
                    "actual": d.actual,
                    "difference": str(d.difference) if d.difference else None,
                    "severity": d.severity.value,
                    "message": d.message,
                }
                for d in self.discrepancies
            ],
            "document_total": str(self.document_total) if self.document_total else None,
            "transaction_total": str(self.transaction_total) if self.transaction_total else None,
            "statement_total": str(self.statement_total) if self.statement_total else None,
        }


class TransactionReconciler:
    """Riconcilia fissato bollato con transazione e estratto conto.

    Verifica coerenza tra:
    - Dati estratti dal fissato bollato (documento PDF)
    - Dati inseriti nella transazione (database)
    - Movimento sul conto corrente (estratto conto)
    """

    def __init__(self, tolerance: Decimal = Decimal("0.02")):
        """Inizializza il riconciliatore.

        Args:
            tolerance: tolleranza per confronto importi (default: 2 centesimi).
        """
        self.tolerance = tolerance

    def reconcile_document_vs_transaction(
        self,
        document_data: dict[str, Any],
        transaction_data: dict[str, Any],
    ) -> ReconciliationResult:
        """Riconcilia dati estratti dal documento con la transazione.

        Args:
            document_data: dati dal parser (ParseResult.to_dict()['fields'])
            transaction_data: dati dalla transazione nel database

        Returns:
            ReconciliationResult con eventuali discrepanze.
        """
        result = ReconciliationResult(tolerance_used=self.tolerance)

        # Confronta campi numerici
        amount_fields = [
            ("net_settlement_amount", "net_settlement_amount", "Importo netto regolamento"),
            ("gross_amount", "gross_amount", "Controvalore lordo"),
            ("accrued_interest", "accrued_interest", "Rateo cedolare"),
            ("bank_commission", "bank_commission", "Commissioni bancarie"),
            ("quantity", "quantity", "Quantità/Nominale"),
            ("unit_price", "unit_price", "Prezzo unitario"),
        ]

        for doc_field, txn_field, label in amount_fields:
            doc_val = self._get_decimal(document_data, doc_field)
            txn_val = self._get_decimal(transaction_data, txn_field)

            if doc_val is None or txn_val is None:
                continue

            diff = abs(doc_val - txn_val)
            if diff > self.tolerance:
                severity = self._classify_severity(diff, doc_val)
                result.discrepancies.append(Discrepancy(
                    field=label,
                    expected=str(doc_val),
                    actual=str(txn_val),
                    difference=diff,
                    severity=severity,
                    message=f"{label}: documento={doc_val}, transazione={txn_val}, diff={diff}",
                ))

        # Confronta date
        for doc_field, txn_field, label in [
            ("trade_date", "trade_date", "Data operazione"),
            ("settlement_date", "settlement_date", "Data regolamento"),
        ]:
            doc_val = document_data.get(doc_field)
            txn_val = transaction_data.get(txn_field)
            if doc_val and txn_val and str(doc_val) != str(txn_val):
                result.discrepancies.append(Discrepancy(
                    field=label,
                    expected=str(doc_val),
                    actual=str(txn_val),
                    severity=DiscrepancySeverity.ERROR,
                    message=f"{label}: documento={doc_val}, transazione={txn_val}",
                ))

        # Confronta ISIN
        doc_isin = document_data.get("isin")
        txn_isin = transaction_data.get("isin")
        if doc_isin and txn_isin and doc_isin != txn_isin:
            result.discrepancies.append(Discrepancy(
                field="ISIN",
                expected=str(doc_isin),
                actual=str(txn_isin),
                severity=DiscrepancySeverity.CRITICAL,
                message=f"ISIN non corrisponde: documento={doc_isin}, transazione={txn_isin}",
            ))

        # Totali per riconciliazione
        result.document_total = self._get_decimal(document_data, "net_settlement_amount")
        result.transaction_total = self._get_decimal(transaction_data, "net_settlement_amount")

        # Determina se è riconciliato
        result.is_reconciled = not result.has_errors
        return result

    def reconcile_with_statement(
        self,
        transaction_amount: Decimal,
        statement_amount: Decimal,
        transaction_date: date | None = None,
        statement_date: date | None = None,
    ) -> ReconciliationResult:
        """Riconcilia totale fissato bollato con movimento estratto conto.

        Verifica che l'importo netto della transazione corrisponda
        al movimento sul conto corrente.

        Args:
            transaction_amount: importo netto dalla transazione
            statement_amount: importo dal movimento in estratto conto
            transaction_date: data operazione
            statement_date: data valuta estratto conto

        Returns:
            ReconciliationResult con esito.
        """
        result = ReconciliationResult(
            tolerance_used=self.tolerance,
            transaction_total=transaction_amount,
            statement_total=statement_amount,
        )

        diff = abs(transaction_amount - statement_amount)
        if diff > self.tolerance:
            severity = self._classify_severity(diff, transaction_amount)
            result.discrepancies.append(Discrepancy(
                field="Importo netto regolamento",
                expected=str(transaction_amount),
                actual=str(statement_amount),
                difference=diff,
                severity=severity,
                message=(
                    f"Totale fissato bollato ({transaction_amount}) ≠ "
                    f"movimento estratto conto ({statement_amount}), diff={diff}"
                ),
            ))

        if transaction_date and statement_date and transaction_date != statement_date:
            result.discrepancies.append(Discrepancy(
                field="Data valuta",
                expected=str(transaction_date),
                actual=str(statement_date),
                severity=DiscrepancySeverity.INFO,
                message=f"Date diverse: operazione={transaction_date}, valuta={statement_date}",
            ))

        result.is_reconciled = not result.has_errors
        return result

    def _get_decimal(self, data: dict, key: str) -> Decimal | None:
        """Estrae un Decimal da un dizionario, gestendo vari formati."""
        val = data.get(key)
        if val is None:
            return None
        if isinstance(val, dict):
            val = val.get("value")
        if val is None:
            return None
        try:
            return Decimal(str(val))
        except Exception:
            return None

    def _classify_severity(self, diff: Decimal, reference: Decimal) -> DiscrepancySeverity:
        """Classifica la gravità di una discrepanza basata su importo relativo."""
        if reference == 0:
            return DiscrepancySeverity.ERROR

        pct = diff / abs(reference)

        if pct > Decimal("0.05"):
            return DiscrepancySeverity.CRITICAL  # > 5%
        if pct > Decimal("0.01"):
            return DiscrepancySeverity.ERROR     # > 1%
        if pct > Decimal("0.001"):
            return DiscrepancySeverity.WARNING   # > 0.1%
        return DiscrepancySeverity.INFO          # ≤ 0.1%
