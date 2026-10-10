"""Jede Zahl des README (Abschnitt "Befunde") wird hier über dieselben Auswertungsfunktionen wie in der App nachgerechnet.

Die Messreihen sind deterministisch (SplitMix64-Pools, SplitMix64-Ziehungen), die Bänder nur Rundungs- und Plattformreserve."""

import numpy as np
import pytest

import abt_constants as C
import abt_evaluation as E

REPS = 4000
Z_CELLS = (1.0, 1.2, 1.4, 1.8)


@pytest.fixture(scope="module")
def cells(pools):
    return {(z, n): E.summarize(pools, z, n, reps=REPS) for z in Z_CELLS for n in C.N_GRID}


def test_effect_of_factor_1_4_and_the_shortage_in_words(pools):
    assert 100 * E.true_effect(pools, 1.4) == pytest.approx(3.49, abs=0.06)
    a, b, red = E.reduction_in_shortage(1.4)
    assert round(100 * a, 1) == 7.5
    assert round(100 * b, 1) == 3.9
    assert round(100 * red) == 47


def test_interval_covers_in_94_to_96_percent_in_all_28_cells(cells):
    cover = [c["coverage"] for c in cells.values()]
    assert len(cover) == 28
    assert min(cover) >= 0.935 and max(cover) <= 0.965


def test_false_alarm_rate_is_4_to_5_5_percent_at_every_size(cells):
    rates = [cells[(1.0, n)]["reject"] for n in C.N_GRID]
    assert min(rates) >= 0.035 and max(rates) <= 0.06
    assert min(rates) == pytest.approx(0.040, abs=0.006)
    assert max(rates) == pytest.approx(0.055, abs=0.006)


def test_units_are_left_skewed_and_pile_up_at_one_hundred_percent(pools):
    def skew(p):
        return float(((p - p.mean()) ** 3).mean() / p.std() ** 3)

    assert skew(pools[1.0]) == pytest.approx(-0.8, abs=0.1)
    assert skew(pools[2.0]) == pytest.approx(-2.3, abs=0.15)
    assert float(np.mean(pools[1.0] == 1.0)) == pytest.approx(0.040, abs=0.006)
    assert float(np.mean(pools[2.0] == 1.0)) == pytest.approx(0.450, abs=0.01)


def test_sample_sizes_normal_formula_against_simulation(pools):
    expected = {1.2: (94, 95), 1.4: (26, 26), 1.8: (11, 12)}
    for z, (normal, sim) in expected.items():
        assert E.normal_formula_n(pools, z) == pytest.approx(normal, abs=1)
        assert E.simulated_n(pools, z, reps=REPS) == pytest.approx(sim, abs=1)


def test_normal_formula_is_within_one_window_of_the_simulation(pools):
    for z in (1.1, 1.2, 1.3, 1.4, 1.6, 1.8, 2.0):
        sim = E.simulated_n(pools, z, reps=REPS)
        assert abs(sim - E.normal_formula_n(pools, z)) <= 1, z


def test_small_samples_miss_the_real_effect_and_exaggerate_it(cells):
    c = cells[(1.2, 10)]
    assert c["reject"] == pytest.approx(0.126, abs=0.01)
    assert 1 - c["reject"] == pytest.approx(0.87, abs=0.011)
    c5 = cells[(1.2, 5)]
    assert c5["reject"] == pytest.approx(0.072, abs=0.01)
    assert c5["exaggeration"] == pytest.approx(3.4, abs=0.15)
    assert cells[(1.2, 100)]["exaggeration"] == pytest.approx(1.1, abs=0.05)
    assert cells[(1.8, 100)]["exaggeration"] == pytest.approx(1.0, abs=0.01)


def test_wrong_sign_rate(cells):
    effect_cells = [c for (z, _n), c in cells.items() if z > 1.0]
    assert max(c["reject_wrong"] for c in effect_cells) <= 0.006
    aa = [c["reject_wrong"] for (z, _n), c in cells.items() if z == 1.0 and _n >= 10]
    assert 0.015 <= min(aa) and max(aa) <= 0.035


def test_sample_size_of_a_normal_formula_documented_value(pools):
    """Die README nennt 26 Fenster je Arm für Faktor 1,4 bei 80 % Teststärke."""
    assert E.normal_formula_n(pools, 1.4) == 26
