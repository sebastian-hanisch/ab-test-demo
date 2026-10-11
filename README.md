# A/B-Test: ist der Unterschied echt? – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-ab-test-demo.streamlit.app/)**

Interaktive Demo zum **Vergleich zweier Regeln im Feldversuch**. **Erstes Stück der Konzepte-Linie „Experimente und
Wirkungsmessung“** im Portfolio von [Sebastian Hanisch](https://sebastianhanisch.net) (Operations Research und Machine
Learning): ein Verfahren, ein wachsendes Beispiel, jedes Folgestück hebt genau eine Annahme auf. Die Linie nimmt die Frage ernst,
die hinter jedem „Verfahren A ist x % besser als B“ der Portfolio-Demos steht: **wann ist ein Unterschied echt?**

Vehikel der ganzen Linie ist ein **Standort mit täglicher Nachbestellung** (Base-Stock-Regel, Wiederbeschaffungszeit zwei Tage,
Zentrallager unbegrenzt; das Bestandsmodell selbst ist Gegenstand von
[forecast-inventory-demo](https://github.com/sebastian-hanisch/forecast-inventory-demo), hier dient es nur als Kulisse).
Regel A fährt den Sicherheitsfaktor z = 1,0, die neue Regel B einen größeren. Kennzahl ist der **Servicegrad** (Anteil der
Nachfrage, der sofort aus dem Lager bedient wird). Eine Einheit des Experiments ist ein **Standort-Fenster**: vier Wochen eines
Standorts, nach vier Wochen Einschwingen mit derselben Regel.

## Kernfrage

Wenn ein Test „signifikant“ sagt, hält dann sein 95-%-Intervall, was es verspricht? Wie oft schlägt er bei gleichen Regeln
fälschlich an, wie oft übersieht er einen echten Effekt, und wie viele Standort-Fenster braucht man?

## Modell und Methodik

- **Vehikel** (`abt_vehicle.py`): Gamma-Poisson-Nachfrage mit Mittel 20 und Varianz 100 je Tag, Bestellung täglich bis zum Niveau
  `S = round(L·μ + z·σ_L)`, Netto-Bestand mit Rückstand. Ein Fenster liefert den Servicegrad Typ 2 (Quote der Summen im
  Fenster). Die exakte Wahrheit des Gleichgewichts liefert `abt_formulas.py` (Summen negativ-binomialer Verteilungen); sie wird
  im Test gegen eine Faltung der Ein-Tages-Verteilung und gegen die Simulation geprüft.
- **Wahrheit des Experiments:** Mittel von je 10 000 simulierten Fenstern je Sicherheitsfaktor
  (`generate_precomputed.py` → `precomputed_pools.json`, SplitMix64, jede Einheit ein eigener Strom). Ein Experiment zieht n
  Fenster je Arm mit Zurücklegen aus den Pools; bei n weit unter 10 000 ist das dasselbe wie n frische Fenster.
- **Test** (`abt_stats.py`): Welch-t-Test für B minus A mit Konfidenzintervall, vektorisiert für viele Experimente; Normalformel
  für den Umfang je Arm.
- **Live:** ein Experiment mit frisch simulierten Fenstern (SplitMix64) und 1 000 Wiederholungen aus den Pools.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py` (4 000 Wiederholungen je Zelle; Fehler der Raten höchstens 0,8 Prozentpunkte).

| Frage | Befund |
|---|---|
| Wie groß ist der Effekt? | Sicherheitsfaktor 1,4 gegen 1,0 hebt den Servicegrad um **3,49 Prozentpunkte**. Als Fehlmenge: von 7,5 % auf 3,9 % der Nachfrage, also **47 %** weniger. |
| Hält das 95-%-Intervall? | **Ja.** In allen 28 gemessenen Zellen (4 Sicherheitsfaktoren × 7 Umfänge von 5 bis 200 Fenstern je Arm) enthält es die Wahrheit in **94 bis 96 %** der Experimente. |
| Schlägt der Test bei gleichen Regeln zu oft an? | **Nein.** Fehlalarmrate **4,0 bis 5,5 %** in allen sieben Umfängen. |
| Trotz schiefer Daten? | Die Fenster-Servicegrade sind links-schief (Schiefe −0,8 bei Faktor 1,0, −2,3 bei Faktor 2,0) und an der Obergrenze gestaucht: **4,0 %** der Fenster haben einen Servicegrad von genau 100 % bei Faktor 1,0, **45,0 %** bei Faktor 2,0. Der Test hält trotzdem. |
| Wie viele Fenster braucht man? | Normalformel und Simulation stimmen überein: Faktor 1,4 braucht **26** Fenster je Arm für 80 % Teststärke (Simulation 26), Faktor 1,2 braucht 94 (Simulation 95), Faktor 1,8 braucht 11 (Simulation 12). |
| Und mit wenigen Fenstern? | Bei Faktor 1,2 und **10 Fenstern je Arm** meldet der Test den echten Vorteil nur in **12,6 %** der Experimente, in den übrigen 87 % steht „nicht signifikant“. Ein nicht signifikantes Ergebnis ist hier kein Beleg für Gleichheit. |
| Was ist mit den signifikanten? | Bei Faktor 1,2 und **5 Fenstern je Arm** schlägt der Test in 7,2 % der Fälle an, und die Schätzung ist dann im Mittel das **3,4-Fache** der wahren Wirkung. Bei 100 Fenstern je Arm ist es das 1,0-Fache. |
| Falsches Vorzeichen? | Bei echtem Effekt höchstens **0,4 %** der Experimente; bei gleichen Regeln die Hälfte der Fehlalarme (2 bis 3 %). |

## Befunde und Korrekturen gegenüber dem Plan

- **Die Vorab-Messreihe (Terminal-Gate der Warteschlangen-Linie, Tagesmittel der Wartezeit) fand dasselbe Muster.** Dort
  deckte das Intervall 93 bis 95 % und der Test war konservativ; auf diesem Vehikel ist es noch besser kalibriert. Der Haken dieses
  Stücks ist deshalb nicht, dass der Test versagt, sondern das, was er nicht verspricht: wenig Daten sehen nichts, und was
  wenige Daten sehen, ist zu groß.
- **Vehikelwechsel.** Vorgesehen war zunächst ein Terminal-Gate der Warteschlangen-Linie (Wartezeit je Tag). Nach dem Einwand
  „schon wieder Warteschlangen“ ist das Vehikel ein Standort mit Bestand; alle Zahlen dieses Stücks sind auf dem neuen Vehikel
  gemessen, nicht übernommen.
- **Die Normalformel trifft hier genau, auf dem Gate lag sie darüber.** Dort verlangte sie 8 bis 15 % mehr Tage als die
  Simulation; der Mittelwert und die Streuung der Tagesmittel koppelten sich stark (Korrelation 0,8 in der Vorab-Messreihe).
  Hier liegt sie höchstens ein Fenster daneben; ob die Kopplung schwächer ist, wurde nicht gemessen.

## Ehrliche Grenzen

| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Der Umfang steht vorher fest** | Wer täglich ansieht und stoppt, bekommt viel mehr Fehlalarme als 5 %. | Zwischenblicke und dauerndes Hinsehen |
| **Man kennt Wirkung und Streuung vorab** | Die Normalformel braucht beides; ein kleiner Pilot streut stark. | Teststärke und Stichprobenumfang |
| **Die Zuteilung lief wie geplant** | Ergebnisabhängiger Verlust von Fenstern verzerrt den Vergleich still. | Gültigkeit der Zuteilung (A/A, Sample-Ratio-Mismatch) |
| **Ein Test, eine Kennzahl** | Viele Kennzahlen oder Varianten erzeugen Zufallstreffer, die beste wird überschätzt. | Viele Kennzahlen: Mehrfachtests und Gewinnerfluch |
| **Einheiten unabhängig und gleichartig** | Persistente Standortunterschiede, Serienkorrelation und Verhältniskennzahlen machen das Intervall zu schmal. | Verhältniskennzahlen und Cluster; Varianzreduktion |
| **Die Verteilung ist harmlos** | Hier hält der Test trotz Schiefe; mit Ausreißern nicht mehr. | Schiefe Daten und Ausreißer |
| **Die Einheiten beeinflussen sich nicht** | Teilen A- und B-Standorte Kundschaft oder Lager, misst der Test nicht die Wirkung des Ausrollens. | Interferenz und Switchback |
| **Man darf randomisieren** | Bei wenigen Einheiten oder ohne Experiment braucht es Vergleichsstandorte oder Logdaten. | Differenz-von-Differenzen und synthetische Kontrolle; Auswertung aus Logdaten |

Dazu kommt **Bandit statt A/B** als Alternative zur festen Zuteilung. Die Zahlen gelten für dieses erfundene Vehikel mit
unabhängigen Fenstern und einem Test pro Experiment; sie sind kein Praxisdatensatz.

## Bezug zu OR

Jede Regeländerung in Disposition, Bestand oder Routing steht vor der Frage, ob sie wirkt und wie lange man messen muss. Die
Demos des Portfolios vergleichen Verfahren auf erzeugten Instanzen und nennen „A ist x % besser als B“; im Betrieb sind die
Ergebnisse Stichproben, und dieselbe Frage nach Streuung und Aufwand stellt sich dort. Das Stück gibt der Disziplin „Prozentvergleiche
mit Basis und Streuung“ ein Zuhause.

## Verwandte Demos im Portfolio

- [output-analysis-demo](https://github.com/sebastian-hanisch/output-analysis-demo) prüft ebenfalls, ob nominale Intervalle
  ihre Abdeckung halten, dort für Simulationsläufe mit stark verwandten Wartezeiten. Hier sind die Einheiten unabhängig.
- [forecast-interval-demo](https://github.com/sebastian-hanisch/forecast-interval-demo): gleiches Muster „hält die Nennabdeckung“,
  für Prognoseintervalle.
- [forecast-inventory-demo](https://github.com/sebastian-hanisch/forecast-inventory-demo): die Base-Stock-Regel des Vehikels.
- [bandit-demo](https://github.com/sebastian-hanisch/bandit-demo): Regret und Auswahlverfahren statt Inferenz.

## Verifikation

- **Vehikel:** Mini-Instanz von Hand gerechnet (`tests/conftest.py`, Tage 20, 60, 10, 25: Nachfrage 95, Fehlmenge 36); Momente
  der Nachfrage; Zweig-Test (der Sicherheitsfaktor wirkt).
- **Orakel** (`tests/test_oracle_ab_test.py`): Servicegrad-Formel gegen Faltung der Ein-Tages-Verteilung und gegen die
  Simulation; Welch-Test gegen `scipy.stats.ttest_ind` einschließlich Intervall; Abdeckung 95 % und Fehlalarm 5 % auf
  Normaldaten.
- **Zufall:** SplitMix64 gegen die bekannten Referenzwerte, vektorisierte gleich skalarer Fassung.
- **Auswertung:** Abdeckung, Fehlalarm, Teststärke und Überschätzung gegen Bänder; Normalformel gegen Simulation.
- **Presets, Oberfläche, Footer:** vollständig, Permalink eingerastet, AppTest-Rauchtest, Footer-Test.
- **Befunde:** jede Zahl dieses READMEs in `tests/test_claims.py`.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `app.py` | Streamlit-App: ein Experiment, tausend Wiederholungen, Stichprobenumfang, Grenzen |
| `abt_constants.py` | Vehikel-Konstanten, Regler-Grenzen, Farben, Presets |
| `abt_rng.py` | SplitMix64, skalar und vektorisiert |
| `abt_vehicle.py` | Standort-Fenster: Nachfrage, Bestandsfortschreibung, Servicegrad |
| `abt_formulas.py` | Exakter Servicegrad des Gleichgewichts |
| `abt_stats.py` | Welch-Test, Konfidenzintervall, Normalformel |
| `abt_evaluation.py` | Experimente aus den Pools, Teststärke, Stichprobenumfang |
| `abt_presets.py` | Permalink (Begrenzen, Einrasten), Presets, Zufalls-Seed-Button |
| `abt_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `generate_precomputed.py`, `precomputed_pools.json` | vorgerechnete Pools (je 10 000 Fenster) |
| `tools/measure_stueck1.py` | die Messreihe vor dem Text |
| `tests/` | Vehikel, Orakel, Statistik, Auswertung, Presets, Befunde, AppTest, Footer |

## Bewusst nicht umgesetzt

- **Mehr als zwei Regeln und mehrere Kennzahlen** (Mehrfachtests): eigenes Stück.
- **Bayes'sche Auswertung, Bandit-Zuteilung, Zwischenblicke:** eigene Stücke der Linie.
- **Praxisdaten:** alle Nachfragen sind erzeugt.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und SciPy (Verteilungsfunktionen).

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Experimente und Wirkungsmessung: A/B bis Logdaten](https://sebastianhanisch.net/konzepte-experimente-wirkungsmessung.html).
