"""Messreihe vor dem Text: Welche Befunde zeigt der Zwei-Gruppen-Vergleich auf dem Vehikel wirklich?"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

import abt_constants as C  # noqa: E402
import abt_evaluation as E  # noqa: E402

pools = E.load_pools()
print("Poolmittel und sd je z (Anteil 100 %):")
for z in C.Z_GRID:
    p = pools[z]
    print(f"  z={z}: mean {p.mean():.4f} sd {p.std(ddof=1):.4f} skew {((p-p.mean())**3).mean()/p.std()**3:+.2f}"
          f"  Anteil 100 %: {np.mean(p == 1.0):.3f}  wahre Wirkung {100*E.true_effect(pools, z):+.2f} Pkt.")

print("\nz    n   | Abdeckung  unter/ueber | Ablehnung (falsch) | Typ M | mittl. Breite (Pkt.)")
for z in (1.0, 1.2, 1.4, 1.8):
    for n in C.N_GRID:
        s = E.summarize(pools, z, n, reps=4000)
        print(f"{z:.1f} {n:4d} | {100*s['coverage']:6.1f} %   {100*s['miss_low']:4.1f} / {100*s['miss_high']:4.1f} | "
              f"{100*s['reject']:5.1f} % ({100*s['reject_wrong']:4.1f} %) | {s['exaggeration']:5.2f} | {100*s['mean_width']:5.2f}")

print("\nn je Arm fuer 80 % Teststaerke: Normalformel gegen Simulation")
for z in (1.1, 1.2, 1.3, 1.4, 1.6, 1.8, 2.0):
    nn = E.normal_formula_n(pools, z)
    ns = E.simulated_n(pools, z, reps=4000)
    print(f"  z={z}: wahre Wirkung {100*E.true_effect(pools, z):.2f} Pkt.  Normalformel {nn}  Simulation {ns}")
