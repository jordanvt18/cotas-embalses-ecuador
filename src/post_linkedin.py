# -*- coding: utf-8 -*-
"""Genera la imagen para el post de LinkedIn (1200x627 px) desde los datos reales."""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constantes import ARCHIVO_COTAS_RAW, RAIZ  # noqa: E402

AZUL = "#1565c0"
ROJO = "#c62828"
TINTA = "#10233f"
SUAVE = "#5a6b82"

df = pd.read_csv(ARCHIVO_COTAS_RAW, parse_dates=["fecha"])
mazar = df[df["embalse"] == "Mazar"].sort_values("fecha")

fig = plt.figure(figsize=(12, 6.27), dpi=100)
gs = fig.add_gridspec(2, 1, height_ratios=[0.62, 2.1], hspace=0.06)

# --- encabezado ---
ax_t = fig.add_subplot(gs[0])
ax_t.axis("off")
ax_t.text(
    0.0, 0.88,
    "¿Cómo estaba realmente el embalse Mazar durante los apagones de 2024?",
    fontsize=17, fontweight="bold", color=TINTA, transform=ax_t.transAxes,
)
ax_t.text(
    0.0, 0.18,
    "Cota diaria medida (msnm) vs. nivel crítico declarado · 2022–2026 · Datos públicos de CELEC SUR",
    fontsize=11, color=SUAVE, transform=ax_t.transAxes,
)

# --- serie ---
ax = fig.add_subplot(gs[1])
ax.plot(mazar["fecha"], mazar["cota_msnm"], color=AZUL, linewidth=1.2)
ax.axhline(2115, color=ROJO, linewidth=1.6)
ax.text(
    mazar["fecha"].iloc[5], 2115.8,
    "nivel crítico declarado: 2115 msnm",
    fontsize=10, color=ROJO, va="bottom",
)

# sombrear noviembre 2024
nov = mazar[(mazar["fecha"] >= "2024-10-15") & (mazar["fecha"] <= "2024-12-15")]
ax.axvspan(pd.Timestamp("2024-10-15"), pd.Timestamp("2024-12-15"), color="#fdecea", zorder=0)
ax.annotate(
    "noviembre 2024:\n24 de 30 días bajo el crítico",
    xy=(pd.Timestamp("2024-11-15"), 2111),
    xytext=(pd.Timestamp("2022-01-15"), 2104.5),
    fontsize=11, color=TINTA, fontweight="bold",
    arrowprops=dict(arrowstyle="->", color=SUAVE, lw=1.2),
)
# sombrear la zona bajo el crítico en la propia serie
ax.fill_between(
    mazar["fecha"], mazar["cota_msnm"], 2115,
    where=(mazar["cota_msnm"] < 2115), color=ROJO, alpha=0.30, interpolate=True,
)

ax.set_ylim(2100, 2158)
ax.set_ylabel("Cota (msnm)", fontsize=10, color=SUAVE)
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.tick_params(colors=SUAVE, labelsize=10)
ax.grid(alpha=0.25)
for lado in ("top", "right"):
    ax.spines[lado].set_visible(False)
for lado in ("left", "bottom"):
    ax.spines[lado].set_color(SUAVE)

# pie con URL
fig.text(
    0.05, 0.015,
    "jordanvt18.github.io/cotas-embalses-ecuador  ·  serie completa, estado en vivo y factsheets trimestrales",
    fontsize=10.5, color="#ffffff",
    bbox=dict(boxstyle="round,pad=0.55", facecolor=AZUL, edgecolor="none"),
)

ruta = RAIZ / "reports" / "figures" / "post_linkedin.png"
fig.savefig(ruta, bbox_inches="tight", facecolor="white")
print("imagen →", ruta)
