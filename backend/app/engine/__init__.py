"""
TitoliEngine — Motore contabile deterministico.

Cuore del sistema: tutti i calcoli finanziari e contabili per titoli di debito
secondo i principi contabili OIC 20, OIC 21, OIC 32 e Art. 2426 c.c.

REGOLA FONDAMENTALE: MAI usare float per importi monetari.
Tutti i calcoli usano decimal.Decimal con precisione 28 cifre.
"""
from decimal import getcontext

# Precisione globale per calcoli finanziari
getcontext().prec = 28
