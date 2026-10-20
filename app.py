"""A/B-Test - ist der Unterschied echt? - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Erstes Stück der Konzepte-Linie "Experimente und Wirkungsmessung": Eine neue Dispositionsregel B wird gegen die bestehende
Regel A getestet, Einheit ist ein Standort-Fenster (vier Wochen). Wahrer Effekt und Wahrheit sind im Vehikel bekannt, deshalb
lässt sich messen, ob Intervall und Test halten, was sie versprechen. Siehe README für die Einordnung in die Linie.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import abt_constants as C
from abt_evaluation import (Settings, load_pools, nearest_z, normal_formula_n, power_curve, reduction_in_shortage,
                            run_experiment, simulated_n, summarize, true_effect)
from abt_presets import (apply_preset, bounds, init_session_state_defaults, load_permalink_settings, randomize_seed,
                         sync_query_params)
from abt_visualization import build_forest, build_histogram, build_interval, build_power, build_strip

st.set_page_config(page_title="A/B-Test – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _pools():
    return load_pools()


@st.cache_data(show_spinner=False)
def _experiment(z, n, seed):
    return run_experiment(Settings(z, n, seed))


@st.cache_data(show_spinner=False)
def _many(z, n):
    return summarize(_pools(), z, n)


@st.cache_data(show_spinner=False)
def _power(z, ns):
    return power_curve(_pools(), z, ns)


@st.cache_data(show_spinner=False)
def _n80(z):
    return normal_formula_n(_pools(), z), simulated_n(_pools(), z)


st.title("🧪 A/B-Test: ist der Unterschied echt?")
st.markdown(
    """
Eine neue **Dispositionsregel B** soll die Fehlmengen eines Standorts senken. Ob sie es tut, zeigt kein einzelner Monat,
denn die Nachfrage schwankt. Ein **A/B-Test** teilt Standort-Fenster (vier Wochen eines Standorts) zufällig auf Regel A und
Regel B auf und fragt: **Ist der gemessene Unterschied größer, als der Zufall allein erklärt?** Hier ist die wahre Wirkung
bekannt, deshalb lässt sich messen, **ob ein Test hält, was er verspricht**: wie oft sein 95-%-Intervall die Wahrheit
enthält, wie oft er bei gleichen Regeln fälschlich anschlägt und wie viele Fenster er für einen echten Effekt braucht.
"""
)

# erklaerseite:einfach:start (erzeugt von tools/set_demo_explainer.py (Website-Repo) aus tools/content/explainers/ab-test-erklaert.json, nicht von Hand ändern)
with st.expander("💬 In einfachen Worten"):
    st.markdown(
        """
Ein Standort will wissen, ob eine neue Bestellregel weniger Fehlmengen bringt als die bisherige. Ein einzelner Monat sagt wenig, denn die Nachfrage schwankt zufällig. Beim **A/B-Test** teilt man viele Vier-Wochen-Abschnitte der Standorte zufällig auf die alte und die neue Regel auf und vergleicht die Ergebnisse. Ein Intervall gibt an, in welchem Bereich die wahre Wirkung vermutlich liegt, und der p-Wert zeigt, ob der Unterschied größer ist, als der Zufall allein erklärt. Die Demo kennt die wahre Wirkung und misst deshalb, wie oft der Test richtig liegt, wie oft er fälschlich anschlägt und wie viele Abschnitte er braucht. Es ist ein stark vereinfachtes Modell mit erfundenen Daten.

[Ausführlich und verständlich erklärt, mit Fachteil](https://sebastianhanisch.net/ab-test-erklaert.html)
        """
    )
# erklaerseite:einfach:end
st.caption(
    "Erstes Stück der Linie „Experimente und Wirkungsmessung“. Jedes Folgestück hebt eine der Annahmen unter „Wo die "
    "Annahmen enden“ auf. Das Vehikel ist ein Standort mit täglicher Nachbestellung; die Kennzahl ist der Servicegrad, also "
    "der Anteil der Nachfrage, der sofort aus dem Lager bedient wird."
)

with st.expander("So funktioniert der Vergleich", expanded=True):
    st.markdown(
        """
- **Das Vehikel:** Ein Standort bestellt täglich nach (Bestellniveau = Bedarf der Wiederbeschaffungszeit plus
  **Sicherheitsfaktor z** mal Standardabweichung). Regel A fährt z = 1,0. Regel B fährt einen größeren Sicherheitsfaktor: mehr
  Sicherheitsbestand, weniger Fehlmengen. Je höher z, desto größer die wahre Wirkung.
- **Eine Einheit:** ein Standort-Fenster von 28 Tagen nach 28 Einschwingtagen mit derselben Regel. Gemessen wird der
  Servicegrad im Fenster. Die Fenster sind unabhängig: jedes hat eigene Nachfragen.
- **Der Test:** Mittelwert von B minus Mittelwert von A, dazu der Standardfehler aus den Streuungen beider Arme
  (**Welch**), daraus ein **95-%-Konfidenzintervall** und ein **p-Wert**. Signifikant heißt hier: p unter 0,05.
- **Was das Intervall verspricht:** Wiederholte man das Experiment oft, enthielten etwa 95 von 100 solcher Intervalle die
  wahre Wirkung. Ob das hier stimmt, ist eine Messfrage und wird unten gemessen.
        """
    )

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
preset_cols = st.columns(len(C.PRESET_ORDER))
for i, name in enumerate(C.PRESET_ORDER):
    with preset_cols[i]:
        st.button(name, key=f"preset_{i}", width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP[name])
st.caption(
    "🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen."
)

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    st.markdown("**Regel B**")
    z = st.slider("Sicherheitsfaktor z von Regel B", *bounds("z_slider"), step=C.Z_STEP, key="z_slider", format="%.1f",
                  help="Regel A fährt z = 1,0. Bei z = 1,0 sind beide Regeln gleich: ein A/A-Test, in dem es nichts zu finden gibt.")
    st.markdown("**Experiment**")
    n = st.slider("Standort-Fenster je Arm", *bounds("n_slider"), step=C.N_STEP, key="n_slider",
                  help="So viele unabhängige Fenster (vier Wochen eines Standorts) bekommt jede Regel.")
    seed = st.number_input("Zufalls-Seed", min_value=bounds("seed_input")[0], max_value=bounds("seed_input")[1], step=1,
                           key="seed_input", help="Bestimmt die Nachfragen des einen Experiments oben.")
    st.button("🎲 Neues Experiment würfeln", on_click=randomize_seed)

z, n, seed = nearest_z(float(z)), int(n), int(seed)
sync_query_params({"z_slider": z, "n_slider": n, "seed_input": seed})

pools = _pools()
truth = true_effect(pools, z)
true_a, true_b = float(pools[nearest_z(C.Z_A)].mean()), float(pools[z].mean())
short_a, short_b, short_red = reduction_in_shortage(z)

st.markdown("---")
st.markdown("## 🧪 Ein Experiment")
with st.spinner("Simuliere …"):
    exp = _experiment(z, n, seed)
w = exp["welch"]
st.caption(
    f"{n} Standort-Fenster je Regel, frisch simuliert. Regel A: z = {C.fmt_num(C.Z_A)}, Regel B: z = {C.fmt_num(z)}. Wahre Wirkung von B "
    f"(aus 10 000 simulierten Fenstern je Regel): **{C.fmt_pp(truth)}** Servicegrad."
)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Regel A, Mittel", C.fmt_pct(float(exp["a"].mean()), 2))
c2.metric("Regel B, Mittel", C.fmt_pct(float(exp["b"].mean()), 2))
c3.metric("Differenz B minus A", C.fmt_pp(w["diff"]), help="Gemessen im Experiment; die wahre Wirkung steht oben.")
c4.metric("p-Wert", C.fmt_num(w["p"], 3), delta="signifikant" if w["p"] < C.ALPHA else "nicht signifikant",
          delta_color="off", delta_arrow="off")
left, right = st.columns([3, 2])
with left:
    st.plotly_chart(build_strip(exp["a"], exp["b"], true_a, true_b, seed), width="stretch", key=f"strip_{z}_{n}_{seed}")
with right:
    st.plotly_chart(build_interval(w, truth), width="stretch", key=f"interval_{z}_{n}_{seed}")
    covered = w["lo"] <= truth <= w["hi"]
    st.caption(
        f"95-%-Intervall: {C.fmt_range_pp(w['lo'], w['hi'])}. "
        + ("Es **enthält** die wahre Wirkung." if covered else "Es **verfehlt** die wahre Wirkung.")
    )
if z > C.Z_A:
    verdict = "signifikant" if w["p"] < C.ALPHA else "nicht signifikant"
    st.info(
        f"**Dieses eine Experiment ist {verdict}.** Die wahre Wirkung ist {C.fmt_pp(truth)}; gemessen wurden "
        f"{C.fmt_pp(w['diff'])}. In Fehlmengen gerechnet: Regel A lässt {C.fmt_pct(short_a)} der Nachfrage unbedient, "
        f"Regel B {C.fmt_pct(short_b)}, also {C.fmt_pct(short_red, 0)} der Fehlmenge von A weniger. Ob das Ergebnis "
        "typisch war, zeigt erst die Wiederholung (nächster Abschnitt)."
    )
else:
    st.info(
        "**Beide Arme fahren dieselbe Regel.** Es gibt nichts zu finden, die wahre Wirkung ist null. Ein "
        "signifikantes Ergebnis ist hier ein Fehlalarm; wie oft das passiert, zeigt die Wiederholung."
    )

st.markdown("---")
st.subheader("📐 Dasselbe Experiment tausendmal: hält der Test, was er verspricht?")
many = _many(z, n)
st.markdown(
    f"Gezogen werden {C.fmt_int(many['reps'])} Experimente mit je {n} Fenstern je Arm aus einem Vorrat von "
    f"{C.fmt_int(C.POOL_SIZE)} simulierten Fenstern je Regel. Jedes wird so ausgewertet wie das eine oben."
)
cols = st.columns(4)
cols[0].metric("Intervall enthält die Wahrheit", C.fmt_pct(many["coverage"]),
               help="Soll-Wert 95 %. Gemessen über alle Wiederholungen.")
if z > C.Z_A:
    cols[1].metric("Signifikant (Teststärke)", C.fmt_pct(many["reject"]),
                   help="Anteil der Experimente, die den echten Effekt als signifikant melden.")
else:
    cols[1].metric("Signifikant (Fehlalarm)", C.fmt_pct(many["reject"]),
                   help="Bei gleichen Regeln soll der Test in etwa 5 % der Fälle anschlagen.")
cols[2].metric("Falsches Vorzeichen", C.fmt_pct(many["reject_wrong"]),
               help="Anteil der Experimente, die einen Unterschied in die falsche Richtung als signifikant melden.")
cols[3].metric("Ø Intervallbreite", C.fmt_num(100 * many["mean_width"], 1) + " Pkt.",
               help="Mittlere Breite des 95-%-Intervalls in Prozentpunkten: wie genau ein einzelnes Experiment die Wirkung eingrenzt.")
left, right = st.columns(2)
with left:
    st.plotly_chart(build_histogram(many["diffs"], many["sig"], truth), width="stretch", key=f"hist_{z}_{n}")
with right:
    st.plotly_chart(build_forest(many["lo"], many["hi"], many["covers"], truth), width="stretch", key=f"forest_{z}_{n}")
    st.caption("Rechts: die ersten 40 Experimente als 95-%-Intervalle; rot verfehlt die wahre Wirkung (gestrichelt).")
if z > C.Z_A:
    miss_note = ""
    if many["reject"] < 0.8:
        miss_note = (
            f" **Bei {n} Fenstern je Arm übersieht der Test den echten Effekt in {C.fmt_pct(1 - many['reject'], 0)} der "
            "Fälle.** Ein nicht signifikantes Ergebnis heißt deshalb nicht, dass es keinen Effekt gibt: es heißt, "
            "dass der Test ihn mit so wenig Daten nicht sicher von Zufall trennt."
        )
    exag = ""
    if many["reject"] < 0.5 and many["exaggeration"] == many["exaggeration"]:
        exag = (
            f" Und wenn er anschlägt, ist die Schätzung im Mittel das {C.fmt_num(many['exaggeration'])}-Fache der "
            "wahren Wirkung: nur die zufällig zu großen Werte werden signifikant."
        )
    if many["coverage"] >= 0.92:
        cover_text = (f"Das 95-%-Intervall enthält die wahre Wirkung in **{C.fmt_pct(many['coverage'])}** der Experimente "
                      "und hält damit sein Versprechen (Soll 95 %, Messfehler bei dieser Wiederholungszahl etwa 0,7 Punkte).")
    else:
        cover_text = (f"Das 95-%-Intervall enthält die wahre Wirkung nur in **{C.fmt_pct(many['coverage'])}** der "
                      "Experimente, also seltener als versprochen.")
    st.success(cover_text + miss_note + exag)
else:
    st.success(
        f"Bei gleichen Regeln schlägt der Test in **{C.fmt_pct(many['reject'])}** der Experimente an (Soll 5 %), und das "
        f"95-%-Intervall enthält die Null in {C.fmt_pct(many['coverage'])}. Gut kalibriert heißt aber nicht fehlerfrei: "
        "Etwa eine von zwanzig Wiederholungen findet einen Unterschied, den es nicht gibt."
    )

st.markdown("---")
st.subheader("📏 Wie viele Standort-Fenster braucht man?")
ns = tuple(sorted(set(C.N_GRID) | {n}))
points = _power(z, ns)
if z > C.Z_A:
    normal_n, sim_n = _n80(z)
    st.markdown(
        "Die **Normalformel** liefert die Fenster je Arm für 80 % Teststärke aus der erwarteten Wirkung und den "
        "Streuungen beider Arme: n = (1,96 + 0,84)² · (σ_A² + σ_B²) / Wirkung²."
    )
    st.plotly_chart(build_power(points, n, z, normal_n), width="stretch", key=f"power_{z}_{n}")
    st.info(
        f"Die wahre Wirkung beträgt {C.fmt_pp(truth)}. Dafür gibt die Normalformel **{normal_n}** Fenster je Arm an, "
        f"die Simulation braucht **{sim_n}**. Das ist der Aufwand, wenn Wirkung und Streuung schon bekannt sind; vor dem "
        "Experiment sind beide nur geschätzt."
    )
else:
    st.plotly_chart(build_power(points, n, z, None), width="stretch", key=f"power_{z}_{n}")
    st.info(
        "Bei z = 1,0 gibt es keine Wirkung: die Kurve zeigt die Fehlalarmrate, und sie liegt bei allen gezeigten "
        "Stichprobengrößen nahe 5 %. Mehr Daten machen den Test nicht strenger, nur genauer."
    )

st.markdown("---")
st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Der Umfang steht vorher fest** | Wer die Daten täglich ansieht und stoppt, sobald p unter 0,05 liegt, bekommt viel mehr Fehlalarme als 5 %. | Zwischenblicke und dauerndes Hinsehen |
| **Man kennt Wirkung und Streuung vorab** | Die Normalformel braucht beides; ein kleiner Pilot streut stark, und knapp signifikante Ergebnisse überschätzen die Wirkung. | Teststärke und Stichprobenumfang |
| **Die Zuteilung lief wie geplant** | Gehen Fenster ergebnisabhängig verloren, verzerrt das den Vergleich, ohne dass der Test es merkt. | Gültigkeit der Zuteilung (A/A, Sample-Ratio-Mismatch) |
| **Ein Test, eine Kennzahl** | Viele Kennzahlen oder Varianten erzeugen Zufallstreffer; die beste Variante wird überschätzt. | Viele Kennzahlen: Mehrfachtests und Gewinnerfluch |
| **Die Einheiten sind unabhängig und gleichartig** | Persistente Unterschiede zwischen Standorten, Serienkorrelation oder Verhältnis-Kennzahlen machen das Intervall zu schmal. | Verhältniskennzahlen und Cluster; Varianzreduktion |
| **Die Verteilung ist harmlos** | Hier ist sie links-schief und an der Obergrenze gestaucht, der Test hält trotzdem. Mit Ausreißern ist das nicht mehr so. | Schiefe Daten und Ausreißer |
| **Die Einheiten beeinflussen sich nicht** | Teilen A- und B-Standorte Kundschaft oder Lager, misst der Test nicht die Wirkung, die man beim Ausrollen bekommt. | Interferenz und Switchback |
| **Man darf randomisieren** | Wo nur wenige Einheiten oder gar kein Experiment möglich sind, braucht es Vergleichsstandorte oder Logdaten. | Differenz-von-Differenzen und synthetische Kontrolle; Auswertung aus Logdaten |
"""
)
st.caption(
    "Die Zahlen oben stammen aus dem Vehikel dieses Stücks (erfundene Parameter, kein Praxisdatensatz); die Aussagen "
    "gelten für diesen Fall mit unabhängigen Fenstern und einem Test pro Experiment."
)

st.markdown("---")
with st.expander("📐 Mathematische Formulierung"):
    # erklaerseite:lesehilfe:start (erzeugt von tools/set_demo_explainer.py (Website-Repo) aus tools/content/explainers/ab-test-erklaert.json, nicht von Hand ändern)
    st.markdown(
        r"""
**Lesehilfe.** Gegeben sind zwei Regeln A und B mit je $n$ simulierten Standort-Fenstern und ihrem gemessenen Servicegrad. Gesucht sind die gemessene Wirkung $\hat\Delta$ mit ihrem Intervall und die Zahl der Fenster je Arm, die für eine gewünschte Teststärke nötig ist.

| Symbol | Bedeutung |
|---|---|
| $\bar x_A$, $\bar x_B$ | Mittelwert des Servicegrads der Fenster in Arm A bzw. B |
| $s_A^2$, $s_B^2$ | gemessene Varianz in Arm A bzw. B |
| $n_A$, $n_B$ | Zahl der Fenster in Arm A bzw. B |
| $\hat\Delta$ | gemessene Wirkung: Mittelwert B minus Mittelwert A |
| $\Delta$ | wahre Wirkung (im Vehikel bekannt) |
| $\widehat{SE}$ | Standardfehler der gemessenen Wirkung |
| $t_{0{,}975,\nu}$, $\nu$ | Quantil der t-Verteilung, Freiheitsgrade nach Welch-Satterthwaite |
| $\alpha$, $1-\beta$ | Signifikanzniveau, Teststärke |
| $z_{1-\alpha/2}$, $z_{1-\beta}$ | Quantile der Normalverteilung zu $\alpha$ (zweiseitig) und zur Teststärke |
| $\sigma_A^2$, $\sigma_B^2$ | Varianz der Fenster in Arm A bzw. B |

[Schritt für Schritt erklärt, mit Herleitung und Literatur](https://sebastianhanisch.net/ab-test-erklaert.html#fachleute)
        """
    )
    # erklaerseite:lesehilfe:end
    st.markdown(
        r"""
**Vehikel.** Tagesnachfrage $D_t$ negativ-binomial (Gamma-Poisson) mit Mittel $\mu = 20$ und Varianz
$\mu + \mu^2/5$. Bestellung täglich bis zum Niveau $S = \operatorname{round}(L\mu + z\,\sigma_L)$ mit
$\sigma_L = \sqrt{L(\mu + \mu^2/5)}$ und Wiederbeschaffungszeit $L = 2$ Tage. Servicegrad Typ 2 im Fenster:
$1 - \sum_t \text{Fehlmenge}_t / \sum_t D_t$. Im Gleichgewicht gilt exakt
$\beta = 1 - \bigl(E[(D_L - S)^+] - E[(D_{L-1} - S)^+]\bigr)/\mu$ mit $D_n$ = Nachfrage von $n$ Tagen.

**Zwei-Gruppen-Test (Welch).** Mit Mittelwerten $\bar x_A, \bar x_B$ und Varianzen $s_A^2, s_B^2$ bei $n_A, n_B$ Einheiten:
$\hat\Delta = \bar x_B - \bar x_A$, $\widehat{SE} = \sqrt{s_A^2/n_A + s_B^2/n_B}$, $t = \hat\Delta/\widehat{SE}$ mit
Welch-Satterthwaite-Freiheitsgraden. Das 95-%-Intervall ist $\hat\Delta \pm t_{0{,}975,\nu}\,\widehat{SE}$.

**Teststärke und Umfang.** Normalnäherung für zweiseitig $\alpha$ und Teststärke $1-\beta$:
$n = (z_{1-\alpha/2} + z_{1-\beta})^2 (\sigma_A^2 + \sigma_B^2)/\Delta^2$ je Arm.

**Messung.** Wahrheit $\Delta$ = Mittel der Pools (je 10 000 Fenster, SplitMix64). Ein Experiment zieht $n$ Fenster je Arm mit
Zurücklegen; Abdeckung, Entscheidungsraten und Überschätzung sind Anteile über 1 000 Wiederholungen.

Implementiert in `abt_vehicle.py` (Vehikel), `abt_formulas.py` (exakter Servicegrad), `abt_stats.py` (Welch, Normalformel),
`abt_evaluation.py` (Experimente, Pools), `generate_precomputed.py` (Pools).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Experimente und Wirkungsmessung: A/B bis Logdaten](https://sebastianhanisch.net/konzepte-experimente-wirkungsmessung.html)."
)
