# TitoliEngine -- Mapping OIC 20 / Normativa Fiscale -> Codice

Questo documento traccia la corrispondenza tra i principi contabili OIC 20 (e la normativa fiscale italiana) e la loro implementazione nel codice sorgente di TitoliEngine.

---

## Indice

1. [Rilevazione iniziale (Costo storico)](#1-rilevazione-iniziale-costo-storico)
2. [Costo ammortizzato e TIR](#2-costo-ammortizzato-e-tir)
3. [Rateo cedolare separato](#3-rateo-cedolare-separato)
4. [Vendita e rimborso](#4-vendita-e-rimborso)
5. [Svalutazione e ripristino](#5-svalutazione-e-ripristino)
6. [Valutazione di fine esercizio](#6-valutazione-di-fine-esercizio)
7. [Incasso cedola](#7-incasso-cedola)
8. [Ratei e risconti di fine esercizio](#8-ratei-e-risconti-di-fine-esercizio)
9. [Ammortamento dello scarto](#9-ammortamento-dello-scarto)
10. [Normativa fiscale](#10-normativa-fiscale)
11. [Nota integrativa](#11-nota-integrativa)
12. [Mappa riassuntiva](#12-mappa-riassuntiva)

---

## 1. Rilevazione iniziale (Costo storico)

### Riferimento OIC 20

**OIC 20, par. 14-30** -- Iscrizione iniziale dei titoli di debito.

Il titolo e' iscritto al costo di acquisto, comprensivo dei costi accessori direttamente attribuibili (commissioni bancarie, bollo, spese). Il rateo cedolare maturato pagato all'acquisto e' rilevato separatamente (par. 50).

**Due metodi:**
- **Costo storico** (bilancio abbreviato/micro, art. 2435-bis c.c.): prezzo + oneri accessori
- **Costo ammortizzato** (bilancio ordinario, par. 37-55): prezzo + costi di transazione, con ammortamento dello scarto tramite TIR

### Implementazione

| Aspetto | File | Funzione chiave |
|---------|------|-----------------|
| Generazione scritture acquisto | `engine/journal/purchase.py` | `PurchaseEntryGenerator.generate_historical_cost()` |
| Costo ammortizzato - acquisto | `engine/journal/purchase.py` | `PurchaseEntryGenerator.generate_amortized_cost()` |
| Calcolo valore iniziale | `engine/amortized_cost.py` | `AmortizedCostEngine.compute_initial_book_value()` |
| Piano dei conti | `engine/journal/templates.py` | `DEFAULT_CHART` (codici conto standard) |
| Costanti e classificazioni | `engine/constants.py` | `Classification`, `ValuationMethod` |

### Test

| Test file | Copertura |
|-----------|-----------|
| `tests/engine/journal/test_purchase.py` | Acquisto a costo storico e ammortizzato |
| `tests/engine/scenarios/test_below_par_purchase.py` | Acquisto sotto la pari con scarto positivo |
| `tests/engine/scenarios/test_above_par_purchase.py` | Acquisto sopra la pari con scarto negativo |
| `tests/engine/scenarios/test_btp_full_lifecycle.py` | Ciclo completo BTP dall'acquisto al rimborso |

### Scrittura contabile tipo (costo storico)

```
Dare: 2520 Titoli immobilizzati        (corso secco + commissioni + bollo)
Dare: 1820 Ratei attivi su titoli      (rateo cedolare maturato)
Avere: 1810 Banca c/c                  (totale esborso)
```

---

## 2. Costo ammortizzato e TIR

### Riferimento OIC 20

**OIC 20, par. 37-55** -- Criterio del costo ammortizzato.

Il costo ammortizzato e' il valore a cui il titolo e' iscritto inizialmente, al netto dei rimborsi di capitale, aumentato o diminuito dell'ammortamento cumulato (calcolato con il TIR) della differenza tra il valore iniziale e il valore a scadenza.

Il **Tasso Interno di Rendimento (TIR)** e' il tasso che rende uguale il valore attuale dei flussi finanziari futuri e il valore di rilevazione iniziale:

```
SUM[ CF_i / (1 + r)^t_i ] = 0
```

dove `t_i = giorni dalla data iniziale / 365.25`

### Implementazione

| Aspetto | File | Funzione chiave |
|---------|------|-----------------|
| Calcolo TIR (Newton-Raphson) | `engine/tir.py` | `TIRCalculator.calculate()` |
| Costruzione flussi di cassa | `engine/tir.py` | `TIRCalculator.build_bond_cash_flows()` |
| Contro-verifica TIR | `engine/tir.py` | `TIRCalculator._verify_result()` |
| Calcolo NPV | `engine/tir.py` | `TIRCalculator.compute_npv()` |
| Motore costo ammortizzato | `engine/amortized_cost.py` | `AmortizedCostEngine` |
| Calcolo tasso effettivo | `engine/amortized_cost.py` | `AmortizedCostEngine.compute_effective_rate()` |
| Valori di periodo | `engine/amortized_cost.py` | `AmortizedCostEngine.compute_period_values()` |
| Piano ammortamento completo | `engine/amortized_cost.py` | `AmortizedCostEngine.generate_amortization_schedule()` |
| Valore contabile a data | `engine/amortized_cost.py` | `AmortizedCostEngine.get_book_value_at_date()` |
| Ammortamento scarto | `engine/spread.py` | `SpreadAmortizationEngine.amortize_effective_rate()` |
| Convenzioni calcolo giorni | `engine/day_count.py` | `DayCountConvention` (ACT/ACT, ACT/360, ACT/365, 30/360) |

### Test

| Test file | Copertura |
|-----------|-----------|
| `tests/engine/test_tir.py` | Newton-Raphson, convergenza, contro-verifica, edge cases |
| `tests/engine/test_amortized_cost.py` | Piano ammortamento, valore a data, convergenza a scadenza |
| `tests/engine/test_spread.py` | Ammortamento scarto per periodo |
| `tests/engine/test_day_count.py` | ACT/ACT, ACT/360, ACT/365, 30/360 |
| `tests/engine/scenarios/test_btp_full_lifecycle.py` | Piano completo BTP con verifica convergenza |
| `tests/engine/scenarios/test_corporate_bond.py` | Obbligazione corporate con costi elevati |

### Garanzie di correttezza

- Precisione: `Decimal` con 28 cifre, mai `float`
- TIR: 12 cifre decimali di precisione (superiore ai 6 richiesti dall'OIC)
- Contro-verifica: dopo il calcolo, il NPV viene ricalcolato e confrontato con zero (tolleranza: 0.01 EUR)
- Convergenza: l'ultimo periodo del piano forza il valore contabile finale = valore di rimborso

---

## 3. Rateo cedolare separato

### Riferimento OIC 20

**OIC 20, par. 50** -- Il rateo cedolare maturato pagato all'acquisto e' rilevato separatamente come rateo attivo. Non fa parte del valore di iscrizione iniziale del titolo.

Alla prima cedola successiva, il rateo da acquisto viene chiuso e la differenza tra cedola incassata e rateo costituisce l'interesse di competenza.

### Implementazione

| Aspetto | File | Funzione chiave |
|---------|------|-----------------|
| Separazione rateo in acquisto | `engine/journal/purchase.py` | Righe separate per rateo e costo titolo |
| Chiusura rateo a prima cedola | `engine/journal/coupon.py` | `CouponEntryGenerator` -- chiusura rateo da acquisto |
| Calcolo rateo maturato | `engine/accruals.py` | Calcolo rateo pro-rata temporis |

### Test

| Test file | Copertura |
|-----------|-----------|
| `tests/engine/journal/test_purchase.py` | Verifica riga rateo separata |
| `tests/engine/journal/test_coupon.py` | Chiusura rateo e calcolo competenza |
| `tests/engine/test_accruals.py` | Calcolo rateo per varie convenzioni giorni |

---

## 4. Vendita e rimborso

### Riferimento OIC 20

**OIC 20, par. 56-62** -- Vendita anticipata e rimborso a scadenza.

**Vendita:** la differenza tra prezzo di vendita (al netto delle commissioni) e valore contabile genera una plusvalenza o minusvalenza. Il rateo maturato e venduto e' rilevato separatamente come interesse.

**Rimborso a scadenza:** il titolo e' scaricato al valore contabile, la differenza con il valore di rimborso genera plus/minusvalenza. Per zero coupon (BOT/CTZ) lo scarto di emissione e' rilevato come interesse.

### Implementazione

| Aspetto | File | Funzione chiave |
|---------|------|-----------------|
| Scritture vendita | `engine/journal/sale.py` | `SaleEntryGenerator` |
| Scritture rimborso/scadenza | `engine/journal/maturity.py` | `MaturityEntryGenerator` |
| Calcolo plus/minusvalenza | `engine/gains_losses.py` | Calcolo gain/loss per vendita e rimborso |

### Test

| Test file | Copertura |
|-----------|-----------|
| `tests/engine/journal/test_sale.py` | Vendita con plus e minus, rateo venduto |
| `tests/engine/journal/test_maturity.py` | Rimborso a pari, sopra/sotto pari, zero coupon |
| `tests/engine/test_gains_losses.py` | Calcolo gain/loss deterministico |
| `tests/engine/scenarios/test_early_sale.py` | Vendita anticipata con costo ammortizzato |
| `tests/engine/scenarios/test_bot_zero_coupon.py` | BOT: scarto emissione e ritenuta |

### Scrittura contabile tipo (vendita con plusvalenza)

```
Dare: 1810 Banca c/c                   (incasso netto)
Dare: 6520 Commissioni vendita          (se presenti)
Avere: 2520 Titoli immobilizzati        (scarico valore contabile)
Avere: 1820 Ratei attivi su titoli      (rateo maturato e venduto)
Avere: 4200 Plusvalenze su titoli       (gain)
```

---

## 5. Svalutazione e ripristino

### Riferimento OIC 20

**OIC 20, par. 63-75** -- Svalutazione per perdite durevoli di valore.

Quando il valore di mercato scende durevolmente sotto il valore contabile, il titolo immobilizzato deve essere svalutato. La svalutazione e' imputata a conto economico (voce D.19.b).

**OIC 20, par. 76-80** -- Ripristino di valore.

Se vengono meno le cause della svalutazione, il valore va ripristinato fino al massimo del valore contabile originale (ante svalutazione). Il ripristino e' imputato a conto economico (voce D.18.b).

### Implementazione

| Aspetto | File | Funzione chiave |
|---------|------|-----------------|
| Scritture svalutazione | `engine/journal/impairment.py` | `ImpairmentEntryGenerator` |
| Scritture ripristino | `engine/journal/impairment.py` | Generazione reversal entry |
| Logica svalutazione/ripristino | `engine/valuation.py` | Confronto book vs market |

### Test

| Test file | Copertura |
|-----------|-----------|
| `tests/engine/scenarios/test_impairment_and_reversal.py` | Svalutazione e successivo ripristino |
| `tests/engine/scenarios/test_year_end_valuation.py` | Valutazione fine esercizio completa |

### Scrittura contabile tipo (svalutazione)

```
Dare: 8400 Svalutazione titoli         (D.19.b CE)
Avere: 2525 Fondo svalutazione titoli  (B.III.3.a.bis SP)
```

### Scrittura contabile tipo (ripristino)

```
Dare: 2525 Fondo svalutazione titoli   (B.III.3.a.bis SP)
Avere: 4300 Ripristino di valore       (D.18.b CE)
```

---

## 6. Valutazione di fine esercizio

### Riferimento OIC 20

**OIC 20, par. 63-80** -- Valutazione titoli a fine esercizio.

Per i titoli immobilizzati:
- Confronto valore contabile (costo ammortizzato o storico) con valore di mercato
- Se mercato < contabile in modo durevole -> svalutazione
- Se precedente svalutazione e mercato risalito -> ripristino (max valore originale)

Per i titoli dell'attivo circolante:
- Valutazione al minore tra costo e valore di mercato (art. 2426, comma 1, n. 9 c.c.)

### Implementazione

| Aspetto | File | Funzione chiave |
|---------|------|-----------------|
| Processo valutazione fine esercizio | `services/valuation_service.py` | `run_year_end_valuation()` |
| Logica confronto book vs market | `engine/valuation.py` | Valutazione per posizione |
| Import prezzi di mercato | `services/valuation_service.py` | `import_market_price()`, `bulk_import_prices()` |
| Endpoint API | `api/valuations.py` | `POST /valuations/year-end` |
| Validazione portafoglio | `engine/validators/portfolio.py` | Validazione coerenza portafoglio |

### Test

| Test file | Copertura |
|-----------|-----------|
| `tests/engine/test_valuation.py` | Logica valutazione unitaria |
| `tests/engine/scenarios/test_year_end_valuation.py` | Processo completo fine esercizio |

---

## 7. Incasso cedola

### Riferimento OIC 20

**OIC 20, par. 50** -- Rilevazione interessi su titoli di debito.

All'incasso della cedola:
- Se esiste un rateo da acquisto, viene chiuso
- La quota di competenza e': `cedola_lorda - rateo_acquisto`
- La ritenuta fiscale e' rilevata come credito verso l'erario

### Implementazione

| Aspetto | File | Funzione chiave |
|---------|------|-----------------|
| Scritture incasso cedola | `engine/journal/coupon.py` | `CouponEntryGenerator` |
| Calcolo ritenuta | `engine/tax.py` | `TaxEngine.calculate_withholding()` |
| Calcolo rateo maturato | `engine/accruals.py` | Rateo pro-rata temporis |

### Test

| Test file | Copertura |
|-----------|-----------|
| `tests/engine/journal/test_coupon.py` | Incasso con/senza rateo da acquisto |
| `tests/engine/test_accruals.py` | Rateo per diverse convenzioni |

### Scrittura contabile tipo

```
Dare: 1810 Banca c/c                   (netto cedola dopo ritenuta)
Dare: 1830 Erario c/ritenute           (ritenuta fiscale)
Avere: 1820 Ratei attivi su titoli     (chiusura rateo acquisto)
Avere: 4100 Interessi attivi su titoli (interesse di competenza)
```

---

## 8. Ratei e risconti di fine esercizio

### Riferimento OIC 20

**OIC 20, par. 50** in combinato con principio di competenza economica.

A fine esercizio vanno rilevati i ratei attivi per gli interessi maturati e non ancora incassati, calcolati pro-rata temporis dalla data ultimo stacco cedola alla data di bilancio.

### Implementazione

| Aspetto | File | Funzione chiave |
|---------|------|-----------------|
| Scritture rateo fine esercizio | `engine/journal/accrual.py` | Generazione rateo a fine anno |
| Calcolo rateo maturato | `engine/accruals.py` | Rateo pro-rata con day count convention |
| Convenzioni calcolo giorni | `engine/day_count.py` | ACT/ACT, ACT/360, ACT/365, 30/360 |

### Test

| Test file | Copertura |
|-----------|-----------|
| `tests/engine/journal/test_accrual.py` | Ratei fine esercizio |
| `tests/engine/test_accruals.py` | Calcolo rateo per varie convenzioni |

---

## 9. Ammortamento dello scarto

### Riferimento OIC 20

**OIC 20, par. 42-45** -- Ammortamento dello scarto di emissione/negoziazione.

Per ogni periodo cedolare:
- **Interessi effettivi** = valore_contabile x TIR x year_fraction
- **Interessi nominali** = nominale x tasso_cedola / frequenza x year_fraction
- **Ammortamento scarto** = effettivi - nominali
- **Nuovo valore contabile** = precedente + ammortamento scarto

### Implementazione

| Aspetto | File | Funzione chiave |
|---------|------|-----------------|
| Ammortamento per periodo | `engine/spread.py` | `SpreadAmortizationEngine.amortize_effective_rate()` |
| Calcolo valori di periodo | `engine/amortized_cost.py` | `AmortizedCostEngine.compute_period_values()` |
| Piano completo | `engine/amortized_cost.py` | `AmortizedCostEngine.generate_amortization_schedule()` |
| Scritture ammortamento | `engine/journal/amortization.py` | Generazione scritture ammortamento scarto |

### Test

| Test file | Copertura |
|-----------|-----------|
| `tests/engine/test_spread.py` | Ammortamento scarto positivo e negativo |
| `tests/engine/test_amortized_cost.py` | Piano completo con convergenza |

---

## 10. Normativa fiscale

### Art. 26 D.P.R. 600/1973 -- Ritenute su interessi

Ritenute alla fonte su interessi e redditi di capitale:
- **12,5%** su titoli di Stato italiani e esteri white list (D.Lgs. 239/1996)
- **26%** su tutti gli altri titoli (obbligazioni corporate, etc.)

### Art. 30 L. 724/1994 -- Societa' di comodo

Test di operativita' per societa' non operative. Coefficienti:
- 2% su titoli e crediti
- 6% su immobili (5% per cat. A/10)
- 15% su altre immobilizzazioni

### Art. 44-67 TUIR -- Classificazione redditi

- Interessi su titoli -> reddito di capitale (art. 44)
- Plusvalenze/minusvalenze -> redditi diversi (art. 67-68)

### Implementazione

| Aspetto | File | Funzione chiave |
|---------|------|-----------------|
| Determinazione regime fiscale | `engine/tax.py` | `TaxEngine.determine_regime()` |
| Calcolo ritenuta | `engine/tax.py` | `TaxEngine.calculate_withholding()` |
| Test societa' di comodo | `engine/tax.py` | `TaxEngine.societa_comodo_test()` |
| Costanti fiscali | `engine/constants.py` | `TAX_RATES`, `WHITE_LIST_COUNTRIES`, `SOCIETA_COMODO_RATES` |
| Report fiscale | `services/report_service.py` | `tax_summary_report()` |
| Endpoint societa' comodo | `api/reports.py` | `POST /reports/societa-comodo` |
| Endpoint tax summary | `api/reports.py` | `GET /reports/tax-summary` |

### Test

| Test file | Copertura |
|-----------|-----------|
| `tests/engine/test_tax.py` | Regime BTP, corporate, white list, PEX, calcolo ritenuta |
| `tests/engine/scenarios/test_societa_comodo.py` | Test operativita' con vari scenari |
| `tests/engine/scenarios/test_bot_zero_coupon.py` | Ritenuta su scarto BOT |

### Regimi fiscali supportati

| Regime | Aliquota | Applicazione |
|--------|----------|--------------|
| `GOVERNMENT_12_5` | 12,5% | BTP, BOT, CCT, CTZ, titoli Stato white list |
| `STANDARD_26` | 26% | Obbligazioni corporate, titoli Stato non white list |
| `PEX` | Variabile | Participation Exemption (art. 87 TUIR) |

---

## 11. Nota integrativa

### Riferimento OIC 20

**OIC 20, par. 81-85** -- Informazioni in nota integrativa.

Prospetto obbligatorio con:
- Saldo iniziale e finale per categoria di titolo
- Movimenti dell'esercizio (acquisti, vendite, scadenze, ammortamenti, svalutazioni, ripristini)
- Fair value complessivo a confronto con valore contabile
- Descrizione dei criteri di valutazione adottati

### Implementazione

| Aspetto | File | Funzione chiave |
|---------|------|-----------------|
| Report OIC 20 per nota integrativa | `services/report_service.py` | `oic20_nota_integrativa()` |
| Endpoint API | `api/reports.py` | `GET /reports/oic20` |

---

## 12. Mappa riassuntiva

Tabella completa delle corrispondenze principio -> codice -> test.

| Principio / Norma | Paragrafi | Modulo engine | Journal generator | Test file |
|---|---|---|---|---|
| Costo storico | OIC 20, par. 14-30 | `constants.py` | `journal/purchase.py` | `test_purchase.py` |
| Costo ammortizzato | OIC 20, par. 37-55 | `amortized_cost.py`, `tir.py`, `spread.py` | `journal/purchase.py` | `test_amortized_cost.py`, `test_tir.py` |
| TIR (Newton-Raphson) | OIC 20, par. 37-45 | `tir.py` | -- | `test_tir.py` |
| Rateo separato | OIC 20, par. 50 | `accruals.py` | `journal/purchase.py`, `journal/coupon.py` | `test_accruals.py`, `test_purchase.py` |
| Incasso cedola | OIC 20, par. 50 | `accruals.py`, `tax.py` | `journal/coupon.py` | `test_coupon.py` |
| Vendita anticipata | OIC 20, par. 56-62 | `gains_losses.py` | `journal/sale.py` | `test_sale.py`, `test_early_sale.py` |
| Rimborso a scadenza | OIC 20, par. 56-62 | `gains_losses.py` | `journal/maturity.py` | `test_maturity.py`, `test_bot_zero_coupon.py` |
| Svalutazione | OIC 20, par. 63-75 | `valuation.py` | `journal/impairment.py` | `test_impairment_and_reversal.py` |
| Ripristino valore | OIC 20, par. 76-80 | `valuation.py` | `journal/impairment.py` | `test_impairment_and_reversal.py` |
| Valutazione fine esercizio | OIC 20, par. 63-80 | `valuation.py` | `journal/impairment.py` | `test_year_end_valuation.py` |
| Nota integrativa | OIC 20, par. 81-85 | -- | -- | (via API) |
| Ratei fine esercizio | OIC 20, par. 50 | `accruals.py`, `day_count.py` | `journal/accrual.py` | `test_accrual.py` |
| Ammortamento scarto | OIC 20, par. 42-45 | `spread.py` | `journal/amortization.py` | `test_spread.py` |
| Ritenute interessi | Art. 26 DPR 600/73 | `tax.py` | `journal/coupon.py` | `test_tax.py` |
| Regime titoli Stato | D.Lgs. 239/1996 | `tax.py`, `constants.py` | -- | `test_tax.py` |
| Societa' di comodo | Art. 30 L. 724/94 | `tax.py` | -- | `test_societa_comodo.py` |
| Plus/minusvalenze | Art. 67-68 TUIR | `gains_losses.py` | `journal/sale.py` | `test_gains_losses.py` |
| Day count conventions | OIC 20, par. 42 | `day_count.py` | -- | `test_day_count.py` |
| Cambio valuta | OIC 26 | `fx.py` | -- | `test_fx.py` |
| Riclassificazione | OIC 20, par. 26 | -- | `journal/reclassification.py` | -- |
| Quadratura dare/avere | Principi generali | `validators/balance.py` | -- | `test_balance_validation.py` |
| Validazione temporale | Principi generali | `validators/temporal.py` | -- | -- |
| Riconciliazione portafoglio | Principi generali | `validators/portfolio.py`, `validators/reconciliation.py` | -- | -- |

---

## Note sulla precisione

- **Tutti i calcoli** usano `decimal.Decimal` con contesto a 28 cifre. Mai `float`.
- **Costante `QUANTIZE_CALC`**: precisione intermedia (10 cifre decimali)
- **Costante `QUANTIZE_CENTS`**: precisione finale (2 cifre decimali, per importi in EUR)
- **TIR**: convergenza con tolleranza `1e-12`, verifica con tolleranza `0.01 EUR`
- **Confronti importi**: tolleranza `0.02 EUR` (2 centesimi) nella riconciliazione
