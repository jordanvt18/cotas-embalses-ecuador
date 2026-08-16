# -*- coding: utf-8 -*-
"""
Visualizaciones del proyecto: series de cota con semáforo de umbrales
oficiales y distancia a nivel crítico.

Los gráficos no incluyen conclusiones editoriales: pintan la serie medida
y las líneas de referencia declaradas en constantes.py. El lector interpreta.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constantes import ARCHIVO_COTAS_RAW, DIR_FIGURAS, EMBALSES  # noqa: E402

plt.rcParams.update(
    {
        "figure.dpi": 110,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)


def cargar_cotas() -> pd.DataFrame:
    df = pd.read_csv(ARCHIVO_COTAS_RAW, parse_dates=["fecha"])
    return df.sort_values(["embalse", "fecha"])


def _banda(ax, minimo, maximo):
    """Pinta la banda operativa normal (min–max) en verde tenue."""
    if minimo is not None and maximo is not None:
        ax.axhspan(minimo, maximo, color="#2e7d32", alpha=0.10, label=f"Banda normal ({minimo:.0f}–{maximo:.0f} msnm)")


def _lineas(ax, embalse_conf):
    for etiqueta, clave, color, estilo in [
        ("Cota mínima", "cota_min", "#f9a825", "--"),
        ("Cota máxima", "cota_max", "#d84315", "--"),
        ("Cota crítica", "cota_critica", "#c62828", "-"),
    ]:
        valor = embalse_conf.get(clave)
        if valor is not None:
            ax.axhline(valor, color=color, linestyle=estilo, linewidth=1.4, label=f"{etiqueta}: {valor:.0f} msnm")


def serie_semaforo(df: pd.DataFrame, embalse: str, ruta: Path | None = None) -> Path:
    """Serie histórica de la cota con umbrales oficiales superpuestos."""
    conf = EMBALSES[embalse]
    datos = df[df["embalse"] == embalse]
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(datos["fecha"], datos["cota_msnm"], color="#1565c0", linewidth=1.0, label="Cota medida (CELEC SUR)")
    _banda(ax, conf.get("cota_min"), conf.get("cota_max"))
    _lineas(ax, conf)
    ax.set_title(f"Embalse {embalse} — cota diaria vs. umbrales operativos de referencia", fontsize=13)
    ax.set_ylabel("Cota (msnm)")
    ax.set_xlabel("Fecha (hora local Ecuador)")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(loc="best", fontsize=9, framealpha=0.9)
    fig.tight_layout()
    ruta = ruta or (DIR_FIGURAS / f"semaforo_{embalse.lower()}.png")
    fig.savefig(ruta)
    plt.close(fig)
    return ruta


def distancia_a_critico(df: pd.DataFrame, embalse: str, ruta: Path | None = None) -> Path | None:
    """Distancia vertical (metros) entre la cota medida y el nivel crítico.

    Solo aplica a embalses con cota crítica declarada (Mazar).
    Valores negativos = cota por debajo del crítico.
    """
    conf = EMBALSES[embalse]
    if conf.get("cota_critica") is None:
        return None
    datos = df[df["embalse"] == embalse].copy()
    datos["distancia_m"] = datos["cota_msnm"] - conf["cota_critica"]
    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.plot(datos["fecha"], datos["distancia_m"], color="#6a1b9a", linewidth=1.0, label="Cota − cota crítica")
    ax.axhline(0, color="#c62828", linewidth=1.5, label=f"Nivel crítico ({conf['cota_critica']:.0f} msnm)")
    ax.fill_between(datos["fecha"], datos["distancia_m"], 0, where=datos["distancia_m"] < 0, color="#c62828", alpha=0.25)
    ax.set_title(f"{embalse}: distancia de la cota medida al nivel crítico declarado", fontsize=13)
    ax.set_ylabel("Metros sobre (+) / bajo (−) el crítico")
    ax.set_xlabel("Fecha (hora local Ecuador)")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(loc="best", fontsize=9)
    fig.tight_layout()
    ruta = ruta or (DIR_FIGURAS / f"distancia_critico_{embalse.lower()}.png")
    fig.savefig(ruta)
    plt.close(fig)
    return ruta


def comparativo_comunicados(
    df: pd.DataFrame,
    comunicados: pd.DataFrame | None,
    embalse: str,
    ruta: Path | None = None,
) -> Path:
    """Serie del embalse con marcadores en las fechas de comunicados oficiales.

    Si comunicados está vacío (aún sin registrar), genera la serie sin
    marcadores — el gráfico sigue siendo útil y honesto.
    """
    conf = EMBALSES[embalse]
    datos = df[df["embalse"] == embalse]
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(datos["fecha"], datos["cota_msnm"], color="#1565c0", linewidth=1.0, label="Cota medida (CELEC SUR)")
    _banda(ax, conf.get("cota_min"), conf.get("cota_max"))
    _lineas(ax, conf)
    if comunicados is not None and len(comunicados):
        fechas = pd.to_datetime(comunicados["fecha"], errors="coerce").dropna()
        ymin, ymax = ax.get_ylim()
        ax.vlines(fechas, ymin, ymax, colors="#37474f", linestyles=":", linewidth=1.2, label="Fechas de comunicados oficiales")
        ax.set_ylim(ymin, ymax)
    ax.set_title(f"{embalse}: cota medida y fechas de comunicados oficiales registrados", fontsize=13)
    ax.set_ylabel("Cota (msnm)")
    ax.set_xlabel("Fecha (hora local Ecuador)")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(loc="best", fontsize=9, framealpha=0.9)
    fig.tight_layout()
    ruta = ruta or (DIR_FIGURAS / f"comunicados_{embalse.lower()}.png")
    fig.savefig(ruta)
    plt.close(fig)
    return ruta


def generar_todas() -> list[Path]:
    """Genera todas las figuras y devuelve las rutas creadas."""
    DIR_FIGURAS.mkdir(parents=True, exist_ok=True)
    df = cargar_cotas()
    comunicados = None
    try:
        com = pd.read_csv(Path(__file__).resolve().parent.parent / "data" / "comunicados" / "comunicados.csv")
        comunicados = com.dropna(subset=["fecha"]) if len(com) else None
    except Exception:
        comunicados = None
    rutas = []
    for embalse in EMBALSES:
        rutas.append(serie_semaforo(df, embalse))
        ruta_dist = distancia_a_critico(df, embalse)
        if ruta_dist:
            rutas.append(ruta_dist)
        rutas.append(comparativo_comunicados(df, comunicados, embalse))
    return rutas


if __name__ == "__main__":
    for ruta in generar_todas():
        print("figura →", ruta)
