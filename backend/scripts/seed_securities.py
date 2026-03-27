"""Seed anagrafica titoli di debito italiani.

Inserisce titoli di Stato italiani (BTP, BOT, CCT, CTZ, BTP Italia, BTP Futura,
BTP Green) e obbligazioni corporate di emittenti italiani di primaria importanza.

I dati sono realistici e basati su emissioni effettive del Ministero dell'Economia
e delle Finanze (MEF) e di emittenti corporate quotati su MOT/EuroTLX.

Riferimenti:
  - MEF — Titoli di Stato in circolazione
  - Borsa Italiana — MOT/EuroTLX
  - OIC 20 "Titoli di debito"

Regime fiscale:
  - Titoli di Stato: ritenuta 12.50% (art. 2 D.Lgs. 239/96)
  - Corporate bonds: ritenuta 26.00% (art. 26 DPR 600/73)

Uso:
    python -m scripts.seed_securities
"""

import asyncio
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.database import async_session_factory
from app.models.security import Security


# ── Titoli di Stato italiani ──
GOVERNMENT_BONDS = [
    # BTP a tasso fisso
    {
        "isin": "IT0005090318",
        "name": "BTP 1.5% 01/06/2025",
        "security_type": "BTP",
        "issuer": "Repubblica Italiana",
        "currency": "EUR",
        "nominal_value": Decimal("100"),
        "coupon_rate": Decimal("1.500000"),
        "coupon_frequency": 2,
        "coupon_dates": {"months": [6, 12], "day": 1},
        "coupon_day_count": "ACT/ACT",
        "maturity_date": date(2025, 6, 1),
        "issue_date": date(2015, 2, 13),
        "issue_price": Decimal("99.7200000000"),
        "tax_regime": "government",
        "withholding_rate": Decimal("0.1250"),
        "is_listed": True,
        "market": "MOT",
    },
    {
        "isin": "IT0005323032",
        "name": "BTP 2.0% 01/02/2028",
        "security_type": "BTP",
        "issuer": "Repubblica Italiana",
        "currency": "EUR",
        "nominal_value": Decimal("100"),
        "coupon_rate": Decimal("2.000000"),
        "coupon_frequency": 2,
        "coupon_dates": {"months": [2, 8], "day": 1},
        "coupon_day_count": "ACT/ACT",
        "maturity_date": date(2028, 2, 1),
        "issue_date": date(2018, 1, 15),
        "issue_price": Decimal("99.6300000000"),
        "tax_regime": "government",
        "withholding_rate": Decimal("0.1250"),
        "is_listed": True,
        "market": "MOT",
    },
    {
        "isin": "IT0005365165",
        "name": "BTP 3.0% 01/08/2029",
        "security_type": "BTP",
        "issuer": "Repubblica Italiana",
        "currency": "EUR",
        "nominal_value": Decimal("100"),
        "coupon_rate": Decimal("3.000000"),
        "coupon_frequency": 2,
        "coupon_dates": {"months": [2, 8], "day": 1},
        "coupon_day_count": "ACT/ACT",
        "maturity_date": date(2029, 8, 1),
        "issue_date": date(2019, 3, 1),
        "issue_price": Decimal("99.4500000000"),
        "tax_regime": "government",
        "withholding_rate": Decimal("0.1250"),
        "is_listed": True,
        "market": "MOT",
    },
    {
        "isin": "IT0005024234",
        "name": "BTP 3.5% 01/03/2030",
        "security_type": "BTP",
        "issuer": "Repubblica Italiana",
        "currency": "EUR",
        "nominal_value": Decimal("100"),
        "coupon_rate": Decimal("3.500000"),
        "coupon_frequency": 2,
        "coupon_dates": {"months": [3, 9], "day": 1},
        "coupon_day_count": "ACT/ACT",
        "maturity_date": date(2030, 3, 1),
        "issue_date": date(2014, 9, 1),
        "issue_price": Decimal("99.1700000000"),
        "tax_regime": "government",
        "withholding_rate": Decimal("0.1250"),
        "is_listed": True,
        "market": "MOT",
    },
    {
        "isin": "IT0003934657",
        "name": "BTP 4.0% 01/02/2037",
        "security_type": "BTP",
        "issuer": "Repubblica Italiana",
        "currency": "EUR",
        "nominal_value": Decimal("100"),
        "coupon_rate": Decimal("4.000000"),
        "coupon_frequency": 2,
        "coupon_dates": {"months": [2, 8], "day": 1},
        "coupon_day_count": "ACT/ACT",
        "maturity_date": date(2037, 2, 1),
        "issue_date": date(2007, 2, 1),
        "issue_price": Decimal("98.4500000000"),
        "tax_regime": "government",
        "withholding_rate": Decimal("0.1250"),
        "is_listed": True,
        "market": "MOT",
    },
    {
        "isin": "IT0003625803",
        "name": "BTP 4.5% 01/03/2036",
        "security_type": "BTP",
        "issuer": "Repubblica Italiana",
        "currency": "EUR",
        "nominal_value": Decimal("100"),
        "coupon_rate": Decimal("4.500000"),
        "coupon_frequency": 2,
        "coupon_dates": {"months": [3, 9], "day": 1},
        "coupon_day_count": "ACT/ACT",
        "maturity_date": date(2036, 3, 1),
        "issue_date": date(2005, 9, 15),
        "issue_price": Decimal("99.0200000000"),
        "tax_regime": "government",
        "withholding_rate": Decimal("0.1250"),
        "is_listed": True,
        "market": "MOT",
    },
    {
        "isin": "IT0004532559",
        "name": "BTP 5.0% 01/09/2040",
        "security_type": "BTP",
        "issuer": "Repubblica Italiana",
        "currency": "EUR",
        "nominal_value": Decimal("100"),
        "coupon_rate": Decimal("5.000000"),
        "coupon_frequency": 2,
        "coupon_dates": {"months": [3, 9], "day": 1},
        "coupon_day_count": "ACT/ACT",
        "maturity_date": date(2040, 9, 1),
        "issue_date": date(2009, 9, 18),
        "issue_price": Decimal("99.6500000000"),
        "tax_regime": "government",
        "withholding_rate": Decimal("0.1250"),
        "is_listed": True,
        "market": "MOT",
    },
    {
        "isin": "IT0005363111",
        "name": "BTP 3.85% 01/09/2049",
        "security_type": "BTP",
        "issuer": "Repubblica Italiana",
        "currency": "EUR",
        "nominal_value": Decimal("100"),
        "coupon_rate": Decimal("3.850000"),
        "coupon_frequency": 2,
        "coupon_dates": {"months": [3, 9], "day": 1},
        "coupon_day_count": "ACT/ACT",
        "maturity_date": date(2049, 9, 1),
        "issue_date": date(2019, 2, 15),
        "issue_price": Decimal("99.4100000000"),
        "tax_regime": "government",
        "withholding_rate": Decimal("0.1250"),
        "is_listed": True,
        "market": "MOT",
    },
    {
        "isin": "IT0005240830",
        "name": "BTP 2.45% 01/09/2033",
        "security_type": "BTP",
        "issuer": "Repubblica Italiana",
        "currency": "EUR",
        "nominal_value": Decimal("100"),
        "coupon_rate": Decimal("2.450000"),
        "coupon_frequency": 2,
        "coupon_dates": {"months": [3, 9], "day": 1},
        "coupon_day_count": "ACT/ACT",
        "maturity_date": date(2033, 9, 1),
        "issue_date": date(2017, 3, 1),
        "issue_price": Decimal("99.5000000000"),
        "tax_regime": "government",
        "withholding_rate": Decimal("0.1250"),
        "is_listed": True,
        "market": "MOT",
    },
    {
        "isin": "IT0005500068",
        "name": "BTP 1.0% 01/07/2027",
        "security_type": "BTP",
        "issuer": "Repubblica Italiana",
        "currency": "EUR",
        "nominal_value": Decimal("100"),
        "coupon_rate": Decimal("1.000000"),
        "coupon_frequency": 2,
        "coupon_dates": {"months": [1, 7], "day": 1},
        "coupon_day_count": "ACT/ACT",
        "maturity_date": date(2027, 7, 1),
        "issue_date": date(2022, 1, 14),
        "issue_price": Decimal("99.8100000000"),
        "tax_regime": "government",
        "withholding_rate": Decimal("0.1250"),
        "is_listed": True,
        "market": "MOT",
    },
    # BOT — zero coupon
    {
        "isin": "IT0005580110",
        "name": "BOT 12M",
        "security_type": "BOT",
        "issuer": "Repubblica Italiana",
        "currency": "EUR",
        "nominal_value": Decimal("100"),
        "coupon_rate": None,
        "coupon_frequency": None,
        "coupon_dates": None,
        "coupon_day_count": "ACT/ACT",
        "maturity_date": date(2025, 10, 14),
        "issue_date": date(2024, 10, 14),
        "issue_price": Decimal("96.5400000000"),
        "tax_regime": "government",
        "withholding_rate": Decimal("0.1250"),
        "is_listed": True,
        "market": "MOT",
    },
    {
        "isin": "IT0005580128",
        "name": "BOT 6M",
        "security_type": "BOT",
        "issuer": "Repubblica Italiana",
        "currency": "EUR",
        "nominal_value": Decimal("100"),
        "coupon_rate": None,
        "coupon_frequency": None,
        "coupon_dates": None,
        "coupon_day_count": "ACT/ACT",
        "maturity_date": date(2025, 4, 14),
        "issue_date": date(2024, 10, 14),
        "issue_price": Decimal("98.2700000000"),
        "tax_regime": "government",
        "withholding_rate": Decimal("0.1250"),
        "is_listed": True,
        "market": "MOT",
    },
    {
        "isin": "IT0005580136",
        "name": "BOT 3M",
        "security_type": "BOT",
        "issuer": "Repubblica Italiana",
        "currency": "EUR",
        "nominal_value": Decimal("100"),
        "coupon_rate": None,
        "coupon_frequency": None,
        "coupon_dates": None,
        "coupon_day_count": "ACT/ACT",
        "maturity_date": date(2025, 1, 14),
        "issue_date": date(2024, 10, 14),
        "issue_price": Decimal("99.1500000000"),
        "tax_regime": "government",
        "withholding_rate": Decimal("0.1250"),
        "is_listed": True,
        "market": "MOT",
    },
    # CCT — tasso variabile
    {
        "isin": "IT0005451361",
        "name": "CCT 01/02/2029",
        "security_type": "CCT",
        "issuer": "Repubblica Italiana",
        "currency": "EUR",
        "nominal_value": Decimal("100"),
        "coupon_rate": Decimal("0.000000"),
        "coupon_frequency": 2,
        "coupon_dates": {"months": [2, 8], "day": 1},
        "coupon_day_count": "ACT/ACT",
        "maturity_date": date(2029, 2, 1),
        "issue_date": date(2021, 10, 15),
        "issue_price": Decimal("100.0000000000"),
        "tax_regime": "government",
        "withholding_rate": Decimal("0.1250"),
        "is_listed": True,
        "market": "MOT",
    },
    {
        "isin": "IT0005311508",
        "name": "CCT 15/04/2026",
        "security_type": "CCT",
        "issuer": "Repubblica Italiana",
        "currency": "EUR",
        "nominal_value": Decimal("100"),
        "coupon_rate": Decimal("0.000000"),
        "coupon_frequency": 2,
        "coupon_dates": {"months": [4, 10], "day": 15},
        "coupon_day_count": "ACT/ACT",
        "maturity_date": date(2026, 4, 15),
        "issue_date": date(2019, 4, 15),
        "issue_price": Decimal("100.0000000000"),
        "tax_regime": "government",
        "withholding_rate": Decimal("0.1250"),
        "is_listed": True,
        "market": "MOT",
    },
    # CTZ — zero coupon
    {
        "isin": "IT0005437147",
        "name": "CTZ 29/01/2026",
        "security_type": "CTZ",
        "issuer": "Repubblica Italiana",
        "currency": "EUR",
        "nominal_value": Decimal("100"),
        "coupon_rate": None,
        "coupon_frequency": None,
        "coupon_dates": None,
        "coupon_day_count": "ACT/ACT",
        "maturity_date": date(2026, 1, 29),
        "issue_date": date(2024, 1, 29),
        "issue_price": Decimal("93.5000000000"),
        "tax_regime": "government",
        "withholding_rate": Decimal("0.1250"),
        "is_listed": True,
        "market": "MOT",
    },
    {
        "isin": "IT0005437154",
        "name": "CTZ 28/06/2027",
        "security_type": "CTZ",
        "issuer": "Repubblica Italiana",
        "currency": "EUR",
        "nominal_value": Decimal("100"),
        "coupon_rate": None,
        "coupon_frequency": None,
        "coupon_dates": None,
        "coupon_day_count": "ACT/ACT",
        "maturity_date": date(2027, 6, 28),
        "issue_date": date(2024, 6, 28),
        "issue_price": Decimal("91.8000000000"),
        "tax_regime": "government",
        "withholding_rate": Decimal("0.1250"),
        "is_listed": True,
        "market": "MOT",
    },
    # BTP Italia — indicizzato inflazione
    {
        "isin": "IT0005497000",
        "name": "BTP Italia 28/06/2030",
        "security_type": "BTP_ITALIA",
        "issuer": "Repubblica Italiana",
        "currency": "EUR",
        "nominal_value": Decimal("100"),
        "coupon_rate": Decimal("1.600000"),
        "coupon_frequency": 2,
        "coupon_dates": {"months": [6, 12], "day": 28},
        "coupon_day_count": "ACT/ACT",
        "maturity_date": date(2030, 6, 28),
        "issue_date": date(2022, 6, 20),
        "issue_price": Decimal("100.0000000000"),
        "tax_regime": "government",
        "withholding_rate": Decimal("0.1250"),
        "is_listed": True,
        "market": "MOT",
    },
    # BTP Futura
    {
        "isin": "IT0005466013",
        "name": "BTP Futura 17/11/2028",
        "security_type": "BTP_FUTURA",
        "issuer": "Repubblica Italiana",
        "currency": "EUR",
        "nominal_value": Decimal("100"),
        "coupon_rate": Decimal("0.750000"),
        "coupon_frequency": 2,
        "coupon_dates": {"months": [5, 11], "day": 17},
        "coupon_day_count": "ACT/ACT",
        "maturity_date": date(2028, 11, 17),
        "issue_date": date(2021, 11, 17),
        "issue_price": Decimal("100.0000000000"),
        "tax_regime": "government",
        "withholding_rate": Decimal("0.1250"),
        "is_listed": True,
        "market": "MOT",
    },
    # BTP Green
    {
        "isin": "IT0005508590",
        "name": "BTP Green 30/04/2035",
        "security_type": "BTP_GREEN",
        "issuer": "Repubblica Italiana",
        "currency": "EUR",
        "nominal_value": Decimal("100"),
        "coupon_rate": Decimal("4.000000"),
        "coupon_frequency": 2,
        "coupon_dates": {"months": [4, 10], "day": 30},
        "coupon_day_count": "ACT/ACT",
        "maturity_date": date(2035, 4, 30),
        "issue_date": date(2023, 4, 5),
        "issue_price": Decimal("99.5500000000"),
        "tax_regime": "government",
        "withholding_rate": Decimal("0.1250"),
        "is_listed": True,
        "market": "MOT",
    },
]

# ── Obbligazioni corporate ──
CORPORATE_BONDS = [
    {
        "isin": "XS2234567890",
        "name": "Enel Finance 1.375% 2025",
        "security_type": "CORPORATE",
        "issuer": "Enel Finance International N.V.",
        "currency": "EUR",
        "nominal_value": Decimal("1000"),
        "coupon_rate": Decimal("1.375000"),
        "coupon_frequency": 1,
        "coupon_dates": {"months": [9], "day": 15},
        "coupon_day_count": "ACT/ACT",
        "maturity_date": date(2025, 9, 15),
        "issue_date": date(2019, 9, 15),
        "issue_price": Decimal("99.3500000000"),
        "tax_regime": "standard",
        "withholding_rate": Decimal("0.2600"),
        "is_listed": True,
        "market": "EuroTLX",
    },
    {
        "isin": "XS2345678901",
        "name": "Intesa Sanpaolo 2.125% 2026",
        "security_type": "CORPORATE",
        "issuer": "Intesa Sanpaolo S.p.A.",
        "currency": "EUR",
        "nominal_value": Decimal("1000"),
        "coupon_rate": Decimal("2.125000"),
        "coupon_frequency": 1,
        "coupon_dates": {"months": [5], "day": 26},
        "coupon_day_count": "ACT/ACT",
        "maturity_date": date(2026, 5, 26),
        "issue_date": date(2020, 5, 26),
        "issue_price": Decimal("99.7800000000"),
        "tax_regime": "standard",
        "withholding_rate": Decimal("0.2600"),
        "is_listed": True,
        "market": "EuroTLX",
    },
    {
        "isin": "XS2456789012",
        "name": "ENI 3.625% 2029",
        "security_type": "CORPORATE",
        "issuer": "Eni S.p.A.",
        "currency": "EUR",
        "nominal_value": Decimal("1000"),
        "coupon_rate": Decimal("3.625000"),
        "coupon_frequency": 1,
        "coupon_dates": {"months": [10], "day": 10},
        "coupon_day_count": "ACT/ACT",
        "maturity_date": date(2029, 10, 10),
        "issue_date": date(2022, 10, 10),
        "issue_price": Decimal("98.9000000000"),
        "tax_regime": "standard",
        "withholding_rate": Decimal("0.2600"),
        "is_listed": True,
        "market": "EuroTLX",
    },
    {
        "isin": "XS2567890123",
        "name": "Unicredit 4.875% 2029",
        "security_type": "CORPORATE",
        "issuer": "UniCredit S.p.A.",
        "currency": "EUR",
        "nominal_value": Decimal("1000"),
        "coupon_rate": Decimal("4.875000"),
        "coupon_frequency": 1,
        "coupon_dates": {"months": [3], "day": 20},
        "coupon_day_count": "ACT/ACT",
        "maturity_date": date(2029, 3, 20),
        "issue_date": date(2023, 3, 20),
        "issue_price": Decimal("99.1200000000"),
        "tax_regime": "standard",
        "withholding_rate": Decimal("0.2600"),
        "is_listed": True,
        "market": "EuroTLX",
    },
    {
        "isin": "XS2678901234",
        "name": "Generali 5.0% 2032",
        "security_type": "CORPORATE",
        "issuer": "Assicurazioni Generali S.p.A.",
        "currency": "EUR",
        "nominal_value": Decimal("1000"),
        "coupon_rate": Decimal("5.000000"),
        "coupon_frequency": 1,
        "coupon_dates": {"months": [7], "day": 8},
        "coupon_day_count": "ACT/ACT",
        "maturity_date": date(2032, 7, 8),
        "issue_date": date(2023, 7, 8),
        "issue_price": Decimal("99.5000000000"),
        "tax_regime": "standard",
        "withholding_rate": Decimal("0.2600"),
        "is_listed": True,
        "market": "EuroTLX",
    },
]


async def seed_securities() -> list[Security]:
    """Inserisce l'anagrafica titoli nel database.

    L'inserimento e idempotente: se un titolo con lo stesso ISIN esiste gia,
    viene saltato.

    Returns:
        Lista degli oggetti Security creati o gia esistenti.
    """
    all_securities = GOVERNMENT_BONDS + CORPORATE_BONDS
    created = []

    async with async_session_factory() as session:
        for sec_data in all_securities:
            # Controlla se esiste gia per ISIN
            stmt = select(Security).where(Security.isin == sec_data["isin"])
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                print(f"  [skip] {sec_data['isin']} — {sec_data['name']} (gia esistente)")
                created.append(existing)
                continue

            security = Security(**sec_data)
            session.add(security)
            created.append(security)
            print(f"  [new]  {sec_data['isin']} — {sec_data['name']}")

        await session.commit()

    gov_count = sum(1 for s in all_securities if s["tax_regime"] == "government")
    corp_count = sum(1 for s in all_securities if s["tax_regime"] == "standard")
    print(f"\nAnagrafica titoli: {len(created)} totali ({gov_count} governativi, {corp_count} corporate)")
    return created


async def main() -> None:
    """Entry point: inserisce tutti i titoli nell'anagrafica."""
    print("Seed anagrafica titoli di debito")
    print("=" * 60)
    await seed_securities()
    print("=" * 60)
    print("Completato.")


if __name__ == "__main__":
    asyncio.run(main())
