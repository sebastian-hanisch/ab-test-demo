"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Scrollen auf dem Handy nicht zoomt."""

import numpy as np
import plotly.graph_objects as go

import abt_constants as C
from abt_rng import uniform_block

_LAYOUT = dict(margin=dict(l=10, r=10, t=40, b=10), height=330, legend=dict(orientation="h", y=-0.2))


def _finish(fig, title, xtitle=None, ytitle=None, **extra):
    fig.update_layout(title=dict(text=title, x=0), xaxis=dict(title=xtitle, fixedrange=True),
                      yaxis=dict(title=ytitle, fixedrange=True), **{**_LAYOUT, **extra})
    return fig


def build_strip(a, b, true_a, true_b, seed):
    """Die Fenster-Servicegrade beider Arme als Punkte, dazu Mittelwert (Raute) und wahrer Mittelwert (gestrichelt), in %."""
    fig = go.Figure()
    for x0, vals, name, color, truth in ((0, a, "Regel A", C.COLOR_A, true_a), (1, b, "Regel B", C.COLOR_B, true_b)):
        jitter = x0 + (uniform_block(seed + x0, len(vals)) - 0.5) * 0.36   # nur Streuung der Punkte in der Zeichnung
        fig.add_trace(go.Scatter(x=jitter, y=100 * np.asarray(vals), mode="markers", name=name,
                                 marker=dict(color=color, size=7, opacity=0.65), hovertemplate="%{y:.1f} %<extra>" + name + "</extra>"))
        fig.add_trace(go.Scatter(x=[x0], y=[100 * float(np.mean(vals))], mode="markers", showlegend=False,
                                 marker=dict(color=color, size=16, symbol="diamond", line=dict(color="white", width=2)),
                                 hovertemplate="Mittel %{y:.2f} %<extra>" + name + "</extra>"))
        fig.add_shape(type="line", x0=x0 - 0.3, x1=x0 + 0.3, y0=100 * truth, y1=100 * truth,
                      line=dict(color=C.COLOR_TRUTH, width=2, dash="dash"))
    fig.update_xaxes(tickmode="array", tickvals=[0, 1], ticktext=["Regel A", "Regel B"], range=[-0.6, 1.6])
    return _finish(fig, "Servicegrad je Standort-Fenster (gestrichelt: wahrer Mittelwert)", None, "Servicegrad in %")


def build_interval(res, truth):
    """Geschätzte Differenz mit 95-%-Intervall; senkrecht: Null und die wahre Wirkung, in Prozentpunkten."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[100 * res["diff"]], y=[0], mode="markers", name="Schätzung",
                             error_x=dict(type="data", symmetric=False, array=[100 * (res["hi"] - res["diff"])],
                                          arrayminus=[100 * (res["diff"] - res["lo"])], thickness=3, width=10, color=C.COLOR_B),
                             marker=dict(color=C.COLOR_B, size=14)))
    fig.add_vline(x=0, line=dict(color="gray", width=1.5), annotation_text="kein Unterschied", annotation_position="top")
    fig.add_vline(x=100 * truth, line=dict(color=C.COLOR_TRUTH, width=2, dash="dash"), annotation_text="wahre Wirkung",
                  annotation_position="bottom")
    fig.update_yaxes(visible=False, range=[-1, 1])
    return _finish(fig, "Differenz B minus A mit 95-%-Intervall", "Prozentpunkte Servicegrad", None, height=210)


def build_histogram(diffs, sig, truth):
    """Geschätzte Differenz in vielen Wiederholungen; signifikante und nicht signifikante getrennt eingefärbt."""
    d = 100 * np.asarray(diffs)
    lo, hi = float(min(d.min(), 0, 100 * truth)), float(max(d.max(), 0, 100 * truth))
    size = max((hi - lo) / 40, 1e-9)
    fig = go.Figure()
    for mask, name, color in ((~sig, "nicht signifikant", C.COLOR_OK), (sig, "signifikant (p unter 0,05)", C.COLOR_B)):
        if mask.any():
            fig.add_trace(go.Histogram(x=d[mask], name=name, marker_color=color, xbins=dict(start=lo, end=hi + size, size=size)))
    fig.update_layout(barmode="stack")
    fig.add_vline(x=0, line=dict(color="gray", width=1.5), annotation_text="kein Unterschied", annotation_position="top left")
    fig.add_vline(x=100 * truth, line=dict(color=C.COLOR_TRUTH, width=2, dash="dash"), annotation_text="wahre Wirkung",
                  annotation_position="top right")
    return _finish(fig, "Geschätzte Differenz in vielen Wiederholungen", "Prozentpunkte Servicegrad (B minus A)", "Experimente")


def build_forest(lo, hi, covers, truth, shown=40):
    """Die ersten Experimente als Intervalle untereinander; rot = verfehlt den wahren Wert."""
    k = min(shown, len(lo))
    fig = go.Figure()
    for i in range(k):
        color = C.COLOR_B if covers[i] else C.COLOR_MISS
        fig.add_trace(go.Scatter(x=[100 * lo[i], 100 * hi[i]], y=[i, i], mode="lines", line=dict(color=color, width=3),
                                 showlegend=False, hoverinfo="skip"))
    fig.add_vline(x=100 * truth, line=dict(color=C.COLOR_TRUTH, width=2, dash="dash"))
    fig.update_yaxes(visible=False, autorange="reversed")
    return _finish(fig, f"Die ersten {k} Experimente mit 95-%-Intervall", "Prozentpunkte Servicegrad", None,
                   height=420)


def build_power(points, n_now, z, normal_n):
    """Teststärke (bzw. Fehlalarmrate bei z = 1,0) gegen die Fenster je Arm."""
    ns = [p[0] for p in points]
    ys = [100 * p[1] for p in points]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ns, y=ys, mode="lines+markers", name="gemessen", line=dict(color=C.COLOR_B, width=3)))
    fig.add_hline(y=80, line=dict(color="gray", dash="dot"), annotation_text="80 %", annotation_position="bottom right")
    fig.add_hline(y=5, line=dict(color="gray", dash="dot"), annotation_text="5 %", annotation_position="top right")
    fig.add_vline(x=n_now, line=dict(color=C.COLOR_A, width=2), annotation_text="Ihre Wahl", annotation_position="top")
    if isinstance(normal_n, int):
        fig.add_vline(x=normal_n, line=dict(color=C.COLOR_TRUTH, dash="dash"), annotation_text="Normalformel (80 %)",
                      annotation_position="bottom")
    fig.update_yaxes(range=[0, 102])
    return _finish(fig, "Anteil signifikanter Experimente je Stichprobenumfang" + (" (Fehlalarmrate)" if z <= C.Z_A else ""),
                   "Standort-Fenster je Arm", "Anteil in %")
