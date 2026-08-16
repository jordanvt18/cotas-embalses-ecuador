# -*- coding: utf-8 -*-
"""
Factsheets trimestrales: una página HTML imprimible por trimestre cerrado,
con los hechos medidos verificables (sin redacción interpretativa).

Salida: docs/factsheets/YYYY-QN.html para cada trimestre completo dentro de
la serie disponible. El sitio principal enlaza el más reciente.

Uso:
    python src/factsheet.py
"""

from __future__ import annotations

import html
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constantes import (  # noqa: E402
    ARCHIVO_COTAS_RAW,
    EMBALSES,
    RAIZ,
    URL_TABLERO_PUBLICO,
    ZONA_HORARIA_ECUADOR,
)

DIR_FACTSHEETS = RAIZ / "docs" / "factsheets"


def _esc(texto) -> str:
    return html.escape(str(texto), quote=True)


def _resumen_embalse(grupo: pd.DataFrame, conf: dict) -> dict:
    serie = grupo.set_index("fecha")["cota_msnm"].asfreq("D")
    n = int(serie.notna().sum())
    minimo, maximo = serie.min(), serie.max()
    return {
        "nombre": conf["central"] if "central" in conf else None,
        "lecturas": n,
        "inicio": serie.dropna().index.min(),
        "fin": serie.dropna().index.max(),
        "cota_inicio": float(serie.dropna().iloc[0]),
        "cota_fin": float(serie.dropna().iloc[-1]),
        "minimo": float(minimo),
        "fecha_minimo": serie.idxmin(),
        "maximo": float(maximo),
        "fecha_maximo": serie.idxmax(),
        "dias_bajo_minimo": int((serie < conf["cota_min"]).sum()),
        "dias_sobre_maximo": int((serie > conf["cota_max"]).sum()),
        "dias_bajo_critico": int((serie < conf["cota_critica"]).sum()) if conf.get("cota_critica") else None,
        "conf": conf,
    }


def _fila_resumen(resumen: dict) -> str:
    variacion = resumen["cota_fin"] - resumen["cota_inicio"]
    criticos = (
        f"<td>{resumen['dias_bajo_critico']}</td>" if resumen["dias_bajo_critico"] is not None else "<td>—</td>"
    )
    return f"""<tr>
  <th>{_esc(resumen['conf'].get('central', ''))}</th>
  <td>{resumen['cota_inicio']:.2f}</td>
  <td>{resumen['cota_fin']:.2f}</td>
  <td>{variacion:+.2f}</td>
  <td>{resumen['minimo']:.2f} <small>({resumen['fecha_minimo'].strftime('%d-%b')})</small></td>
  <td>{resumen['maximo']:.2f} <small>({resumen['fecha_maximo'].strftime('%d-%b')})</small></td>
  <td>{resumen['dias_bajo_minimo']}</td>{criticos}
  <td>{resumen['dias_sobre_maximo']}</td>
</tr>"""


ESTILO = """
  body { font-family: Georgia, serif; color:#1a2332; margin:2rem auto; max-width:52rem; line-height:1.55; padding:0 1rem; }
  h1 { font-size:1.4rem; }
  h2 { font-size:1.05rem; border-bottom:1px solid #ccd4e0; padding-bottom:.3rem; margin-top:1.6rem; }
  table { border-collapse:collapse; width:100%; font-size:.82rem; }
  th, td { border:1px solid #d7dde7; padding:.3rem .5rem; text-align:center; }
  thead th { background:#eef2f8; }
  .nota { color:#5a6b82; font-size:.85rem; }
  .principio { border-left:4px solid #1565c0; padding:.5rem 1rem; background:#f4f7fb; }
  @media print { body { margin:0; } .no-imprimir { display:none; } }
"""


def generar_pagina(trimestre: pd.Period, df: pd.DataFrame) -> Path:
    inicio = trimestre.to_timestamp()
    fin = trimestre.end_time
    datos = df[(df["fecha"] >= inicio.tz_localize(None)) & (df["fecha"] <= fin.tz_localize(None))]

    filas = []
    tarjetas = []
    for embalse, conf in EMBALSES.items():
        grupo = datos[datos["embalse"] == embalse]
        if grupo.empty:
            continue
        resumen = _resumen_embalse(grupo, conf)
        resumen["conf"]["central"] = conf.get("central", embalse)
        filas.append(_fila_resumen(resumen))

    etiqueta = f"{trimestre.year}-Q{trimestre.quarter}"
    documento = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Factsheet {etiqueta} · cotas de embalses del Ecuador</title>
<style>{ESTILO}</style></head>
<body>
<h1>Factsheet trimestral · {etiqueta}</h1>
<p class="nota">Cotas diarias (msnm, medianoche hora Ecuador) medidas por el SCADA de CELEC SUR y
recolectadas por <a href="../index.html">cotas-embalses-ecuador</a>. Hechos verificables; sin conclusiones editoriales.</p>
<p class="principio">Principio del proyecto: los datos se presentan; las conclusiones son del lector.</p>

<h2>Resumen por embalse</h2>
<table>
<thead><tr><th>Embalse</th><th>Cota inicio</th><th>Cota fin</th><th>Δ trimestre</th>
<th>Mínimo</th><th>Máximo</th><th>Días &lt; mínima</th><th>Días &lt; crítica</th><th>Días &gt; máxima</th></tr></thead>
<tbody>{''.join(filas)}</tbody>
</table>

<h2>Umbrales de referencia (msnm)</h2>
<table>
<thead><tr><th>Embalse</th><th>Mínima</th><th>Crítica</th><th>Máxima</th></tr></thead>
<tbody>
{''.join(f"<tr><th>{_esc(e)}</th><td>{c['cota_min']:.0f}</td><td>{c['cota_critica'] if c.get('cota_critica') else '—'}</td><td>{c['cota_max']:.0f}</td></tr>" for e, c in EMBALSES.items())}
</tbody>
</table>

<h2>Verificación</h2>
<p class="nota">Serie completa: <a href="../datos/cotas_historico.csv">cotas_historico.csv</a> ·
Fuente primaria: <a href="{_esc(URL_TABLERO_PUBLICO)}" target="_blank" rel="noopener">tablero oficial CELEC SUR</a> ·
Zona horaria: {_esc(ZONA_HORARIA_ECUADOR)}.</p>
<p class="no-imprimir nota"><a href="../index.html">← volver al sitio</a></p>
</body></html>"""
    DIR_FACTSHEETS.mkdir(parents=True, exist_ok=True)
    ruta = DIR_FACTSHEETS / f"{etiqueta}.html"
    ruta.write_text(documento, encoding="utf-8")
    return ruta


def generar_todas() -> list[Path]:
    df = pd.read_csv(ARCHIVO_COTAS_RAW, parse_dates=["fecha"])
    hoy = pd.Timestamp.now(tz=df["fecha"].dt.tz) if df["fecha"].dt.tz else pd.Timestamp.now()
    trimestres = pd.period_range(df["fecha"].min(), (hoy - pd.offsets.QuarterEnd(1)).normalize(), freq="Q")
    rutas = []
    for trimestre in trimestres:
        rutas.append(generar_pagina(trimestre, df))
    return rutas


if __name__ == "__main__":
    rutas = generar_todas()
    print(f"factsheets → {len(rutas)} páginas en {DIR_FACTSHEETS}")
    for ruta in rutas[-3:]:
        print("  …", ruta.name)
