"""Auswertung: ein Experiment live, viele Experimente aus dem vorgerechneten Pool, Teststärke und Stichprobenumfang.

Der Pool eines Sicherheitsfaktors z ist eine große Menge unabhängiger Standort-Fenster (`generate_precomputed.py`, SplitMix64).
Ein "Experiment" zieht n Fenster je Arm mit Zurücklegen aus dem Pool; das ist für n weit unter der Poolgröße dasselbe wie n frische
Fenster, und die Wahrheit (Poolmittel) ist exakt die Wahrheit der Population, aus der gezogen wird."""

import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

import abt_constants as C
import abt_stats as S
from abt_rng import uniform_block
from abt_vehicle import run_units

PRECOMPUTED = Path(__file__).resolve().parent / "precomputed_pools.json"


@dataclass(frozen=True)
class Settings:
    z: float = C.DEFAULT_Z
    n: int = C.DEFAULT_N
    seed: int = C.DEFAULT_SEED


def load_pools(path=PRECOMPUTED):
    """{z: Array der Fenster-Servicegrade}; z auf eine Nachkommastelle gerundet."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {round(float(k), 1): np.asarray(v, dtype=float) for k, v in data["pools"].items()}


def nearest_z(z):
    return min(C.Z_GRID, key=lambda g: abs(g - z))


def true_effect(pools, z_b):
    """Wahre Wirkung von Regel B gegenüber A: Mittel der Pools, B minus A (Anteil, positiv = B besser)."""
    return float(pools[nearest_z(z_b)].mean() - pools[nearest_z(C.Z_A)].mean())


def run_experiment(settings):
    """Ein Experiment mit frisch simulierten Standort-Fenstern (SplitMix64): n je Arm, Welch-Test."""
    a = np.asarray(run_units(C.Z_A, settings.n, 1_000_003 * (settings.seed + 1) + 11))
    b = np.asarray(run_units(settings.z, settings.n, 1_000_003 * (settings.seed + 1) + 977))
    return {"a": a, "b": b, "welch": S.welch(a, b)}


def _indices(pool_size, count, seed):
    return np.minimum((uniform_block(seed, count) * pool_size).astype(np.int64), pool_size - 1)


def draw_experiments(pool_a, pool_b, n, reps, seed):
    """`reps` Experimente mit je n Fenstern je Arm (mit Zurücklegen aus den Pools), deterministisch aus `seed`."""
    ia = _indices(len(pool_a), reps * n, seed).reshape(reps, n)
    ib = _indices(len(pool_b), reps * n, seed + 7_919).reshape(reps, n)
    return pool_a[ia], pool_b[ib]


def experiment_seed(z, n, tag=0):
    return 5_000_000 + 10_007 * int(round(z * 10)) + 101 * n + 13 * tag


def summarize(pools, z_b, n, reps=C.LIVE_REPS, alpha=C.ALPHA, tag=0):
    """Viele Experimente bei (z_b, n): Abdeckung des 95-%-Intervalls, Entscheidungsraten, Streuung der Schätzung."""
    z_b = nearest_z(z_b)
    pool_a, pool_b = pools[nearest_z(C.Z_A)], pools[z_b]
    a, b = draw_experiments(pool_a, pool_b, n, reps, experiment_seed(z_b, n, tag))
    r = S.welch_batch(a, b, conf=1 - alpha)
    truth = true_effect(pools, z_b)
    sig = r["p"] < alpha
    covers = (r["lo"] <= truth) & (truth <= r["hi"])
    pos = sig & (r["diff"] > 0)
    neg = sig & (r["diff"] < 0)
    out = {
        "z": z_b, "n": n, "reps": reps, "truth": truth,
        "coverage": float(covers.mean()),
        "miss_low": float((r["hi"] < truth).mean()),      # Intervall komplett unter der Wahrheit
        "miss_high": float((r["lo"] > truth).mean()),     # Intervall komplett über der Wahrheit
        "reject": float(sig.mean()),
        "reject_right": float(pos.mean()),
        "reject_wrong": float(neg.mean()),
        "mean_diff": float(r["diff"].mean()),
        "sd_diff": float(r["diff"].std(ddof=1)),
        "mean_width": float((r["hi"] - r["lo"]).mean()),
        "diffs": r["diff"],
        "lo": r["lo"], "hi": r["hi"], "p": r["p"], "sig": sig, "covers": covers,
    }
    if sig.any() and truth != 0:
        out["mean_diff_sig"] = float(np.abs(r["diff"][sig]).mean())
        out["exaggeration"] = out["mean_diff_sig"] / abs(truth)
    else:
        out["mean_diff_sig"] = float("nan")
        out["exaggeration"] = float("nan")
    return out


def power_curve(pools, z_b, n_values=C.N_GRID, reps=C.LIVE_REPS):
    """Anteil signifikanter Experimente je n (Teststärke; bei z_b = 1,0 die Fehlalarmrate)."""
    return [(n, summarize(pools, z_b, n, reps)["reject"]) for n in n_values]


def normal_formula_n(pools, z_b, power=0.8):
    """Normalformel: Fenster je Arm für die gewünschte Teststärke, aus der wahren Wirkung und den Streuungen der Pools."""
    z_b = nearest_z(z_b)
    sd_a = float(pools[nearest_z(C.Z_A)].std(ddof=1))
    sd_b = float(pools[z_b].std(ddof=1))
    return S.n_per_arm_normal(true_effect(pools, z_b), sd_a, sd_b, C.ALPHA, power)


def simulated_n(pools, z_b, power=0.8, reps=C.LIVE_REPS, n_max=400):
    """Kleinstes n (Raster 1, 2, ..., 60, dann Schritte von 5), bei dem die gemessene Teststärke `power` erreicht."""
    grid = list(range(2, 61)) + list(range(65, n_max + 1, 5))
    for n in grid:
        if summarize(pools, z_b, n, reps, tag=3)["reject"] >= power:
            return n
    return None


def reduction_in_shortage(z_b):
    """Wirkung in der Sprache der Fehlmenge: Anteil der Fehlmenge, der gegenüber Regel A wegfällt (Formelwerte)."""
    import abt_formulas as F
    a, b = F.shortage_rate(C.Z_A), F.shortage_rate(z_b)
    return a, b, 1 - b / a
