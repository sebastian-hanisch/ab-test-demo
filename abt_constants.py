"""Konstanten: Vehikel, Regler-Grenzen, Farben, Presets. Das Vehikel (ein Standort-Fenster) ist das der ganzen Linie."""

# Vehikel: ein Standort, tägliche Nachbestellung (Order-up-to), Wiederbeschaffungszeit 2 Tage, Zentrallager unbegrenzt.
BASE_MEAN = 20.0          # mittlere Tagesnachfrage des Standorts (Stück)
DISP = 5                  # Dispersion der negativ-binomialen Tagesnachfrage (ganzzahlig: Gamma(5) = Summe von 5 Exponentialzahlen)
LEAD = 2                  # Wiederbeschaffungszeit in Tagen
BURN_DAYS = 28            # Einschwingtage vor dem Auswertefenster (gleiche Regel wie im Fenster)
WINDOW_DAYS = 28          # Auswertefenster: vier Wochen = ein "Standort-Fenster" = eine Einheit des Experiments
Z_A = 1.0                 # Sicherheitsfaktor der bestehenden Regel A

Z_MIN, Z_MAX, DEFAULT_Z = 1.0, 2.0, 1.4      # Regel B: Sicherheitsfaktor (1,0 = identisch mit A = A/A-Test)
Z_STEP = 0.1
Z_GRID = tuple(round(Z_MIN + i * Z_STEP, 1) for i in range(int(round((Z_MAX - Z_MIN) / Z_STEP)) + 1))
N_MIN, N_MAX, DEFAULT_N, N_STEP = 5, 200, 30, 5   # Standort-Fenster je Arm
SEED_MAX, DEFAULT_SEED = 999999, 35
N_GRID = (5, 10, 20, 30, 50, 100, 200)        # vorgerechnete Messreihen
POOL_SIZE = 10000         # Einheiten je Pool (je Sicherheitsfaktor)
REPS = 2000               # Wiederholte Experimente je Zelle der Messreihen
ALPHA = 0.05
LIVE_REPS = 1000          # Wiederholungen der Live-Auswertung (aus dem Pool gezogen)

COLOR_A = "#4c78a8"
COLOR_B = "#2F6B65"
COLOR_TRUTH = "#d95f02"
COLOR_MISS = "#c0392b"
COLOR_OK = "rgba(120,120,120,0.55)"

PRESETS = {
    "Echter Effekt, mittlere Stichprobe (Voreinstellung)": {"z": DEFAULT_Z, "n": DEFAULT_N, "seed": DEFAULT_SEED},
    "Kein Unterschied (A/A)": {"z": 1.0, "n": DEFAULT_N, "seed": DEFAULT_SEED},
    "Kleiner Effekt, wenig Daten": {"z": 1.2, "n": 10, "seed": DEFAULT_SEED},
    "Großer Effekt, viele Daten": {"z": 1.8, "n": 100, "seed": DEFAULT_SEED},
}
PRESET_ORDER = tuple(PRESETS)
PRESET_HELP = {
    "Echter Effekt, mittlere Stichprobe (Voreinstellung)": "Regel B mit Sicherheitsfaktor 1,4 gegen Regel A mit 1,0; 30 Standort-Fenster je Arm.",
    "Kein Unterschied (A/A)": "Beide Arme fahren dieselbe Regel: jedes signifikante Ergebnis ist ein Fehlalarm.",
    "Kleiner Effekt, wenig Daten": "Sicherheitsfaktor 1,2 gegen 1,0, nur 10 Standort-Fenster je Arm: der Effekt ist da, der Test sieht ihn oft nicht.",
    "Großer Effekt, viele Daten": "Sicherheitsfaktor 1,8 gegen 1,0 mit 100 Standort-Fenstern je Arm: der Normalfall, in dem alles stimmt.",
}


def fmt_pct(x, digits=1):
    """Anteil (0..1) als Prozentzahl mit Dezimalkomma, z. B. 0,934 -> '93,4 %'."""
    return f"{100 * x:.{digits}f}".replace(".", ",") + " %"


def fmt_pp(x, digits=2):
    """Differenz in Prozentpunkten (aus Anteilen 0..1) mit Vorzeichen und Dezimalkomma."""
    return f"{100 * x:+.{digits}f}".replace(".", ",") + " Prozentpunkte"


def fmt_num(x, digits=1):
    return f"{x:.{digits}f}".replace(".", ",")


def fmt_int(x):
    """Ganzzahl mit Leerzeichen als Tausendertrenner."""
    return f"{int(x):,}".replace(",", " ")


def fmt_range_pp(lo, hi, digits=2):
    """Bereich in Prozentpunkten (aus Anteilen 0..1): '+1,52 bis +5,60 Prozentpunkte'."""
    return (f"{100 * lo:+.{digits}f}".replace(".", ",") + " bis " + f"{100 * hi:+.{digits}f}".replace(".", ",")
            + " Prozentpunkte")
