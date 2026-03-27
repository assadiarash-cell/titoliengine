"""Modello anagrafica titoli.

Contiene tutti i dati statici di un titolo di debito:
ISIN, tipo, cedola, scadenza, regime fiscale, ecc.
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, TimestampMixin, UUIDPrimaryKeyMixin

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.portfolio import PortfolioPosition
    from app.models.transaction import Transaction
    from app.models.valuation import MarketPrice


class Security(UUIDPrimaryKeyMixin, TimestampMixin, BaseModel):
    """Anagrafica titolo di debito.

    Riferimento: schema DB sezione 2 — tabella securities.
    """

    __tablename__ = "securities"

    # Identificazione
    isin: Mapped[str] = mapped_column(String(12), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    security_type: Mapped[str] = mapped_column(String(50), nullable=False)
    issuer: Mapped[str | None] = mapped_column(String(255))
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, server_default="EUR"
    )

    # Valore nominale
    nominal_value: Mapped[Decimal] = mapped_column(
        Numeric(20, 10), nullable=False, server_default="100"
    )

    # Dati cedola (NULL per zero coupon)
    coupon_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    coupon_frequency: Mapped[int | None] = mapped_column(Integer)
    coupon_dates: Mapped[dict | None] = mapped_column(JSONB)
    coupon_day_count: Mapped[str] = mapped_column(
        String(20), server_default="ACT/ACT"
    )

    # Dati scadenza
    maturity_date: Mapped[date | None] = mapped_column(Date)
    issue_date: Mapped[date | None] = mapped_column(Date)
    issue_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 10))

    # Regime fiscale
    tax_regime: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="standard"
    )
    withholding_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, server_default="0.2600"
    )

    # Classificazione
    is_listed: Mapped[bool] = mapped_column(Boolean, server_default="true")
    market: Mapped[str | None] = mapped_column(String(50))

    # Relationships
    portfolio_positions: Mapped[list["PortfolioPosition"]] = relationship(
        back_populates="security"
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="security"
    )
    market_prices: Mapped[list["MarketPrice"]] = relationship(
        back_populates="security"
    )
