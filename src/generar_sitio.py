# -*- coding: utf-8 -*-
"""
Generador del sitio estático para GitHub Pages.

Produce docs/index.html a partir de los datos locales (sin llamadas de red):
lecturas más recientes, figuras semáforo, contexto trimestral y enlaces a
los CSV publicados. El sitio es determinista y neutro: presenta datos,
no conclusiones.

Uso:
    python src/generar_sitio.py
"""

from __future__ import annotations

import html
import shutil
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from alertas import evaluar_estado  # noqa: E402
from constantes import (  # noqa: E402
    ARCHIVO_COTAS_PROCESADAS,
    ARCHIVO_COTAS_RAW,
    ARCHIVO_GENERACION,
    DIR_FIGURAS,
    EMBALSES,
    RAIZ,
    URL_TABLERO_PUBLICO,
    ZONA_HORARIA_ECUADOR,
)

DIR_SITIO = RAIZ / "docs"
DIR_SITIO_FIGURAS = DIR_SITIO / "figuras"
DIR_SITIO_DATOS = DIR_SITIO / "datos"
DIR_FACTSHEETS = DIR_SITIO / "factsheets"


def _esc(texto: str) -> str:
    return html.escape(str(texto), quote=True)


def cargar_datos() -> pd.DataFrame:
    df = pd.read_csv(ARCHIVO_COTAS_RAW, parse_dates=["fecha"])
    return df.sort_values(["embalse", "fecha"])


def tarjeta_embalse(embalse: str, fila: pd.Series) -> str:
    conf = EMBALSES[embalse]
    dentro = conf["cota_min"] <= fila["cota_msnm"] <= conf["cota_max"]
    estado = "Dentro de la banda normal de operación" if dentro else "Fuera de la banda normal de operación"
    clase = "tarjeta-estado ok" if dentro else "tarjeta-estado fuera"
    detalle = [f"mínima {conf['cota_min']:.0f} · máxima {conf['cota_max']:.0f} msnm"]
    if conf.get("cota_critica"):
        distancia = fila["cota_msnm"] - conf["cota_critica"]
        detalle.append(f"crítica {conf['cota_critica']:.0f} msnm (a {distancia:+.2f} m)")
    return f"""
      <article class="tarjeta">
        <h3>{_esc(embalse)}</h3>
        <p class="cota">{fila['cota_msnm']:.2f} <span class="unidad">msnm</span></p>
        <p class="fecha-lectura">lectura del {fila['fecha'].strftime('%Y-%m-%d')} (medianoche hora Ecuador)</p>
        <p class="{clase}">{_esc(estado)}</p>
        <p class="detalle">{' · '.join(detalle)}</p>
      </article>"""


def tabla_trimestral(df: pd.DataFrame) -> str:
    tabla = df.pivot_table(index="fecha", columns="embalse", values="cota_msnm", aggfunc="last")
    trimestral = tabla.resample("QS").agg(["mean", "min", "max"]).tail(6).round(2)
    trimestral.index = trimestral.index.to_period("Q").strftime("%Y-Q%q")
    filas = []
    for indice, fila in trimestral.iterrows():
        celdas = "".join(
            f"<td>{fila[(embalse, 'mean')]:.2f} / {fila[(embalse, 'min')]:.2f} / {fila[(embalse, 'max')]:.2f}</td>"
            for embalse in EMBALSES
        )
        filas.append(f"<tr><th>{_esc(str(indice))}</th>{celdas}</tr>")
    encabezado = "".join(f"<th>{_esc(e)}<br><small>media / mín / máx</small></th>" for e in EMBALSES)
    return f"""
    <table>
      <thead><tr><th>Trimestre</th>{encabezado}</tr></thead>
      <tbody>{''.join(filas)}</tbody>
    </table>"""


def banner_estado() -> str:
    """Chips de estado factual por embalse (alimentan el encabezado del sitio)."""
    estado = evaluar_estado()
    clases = {
        "dentro_de_banda": "chip ok",
        "cerca_del_minimo": "chip cerca",
        "cerca_del_maximo": "chip cerca",
        "bajo_minimo": "chip fuera",
        "sobre_maximo": "chip fuera",
        "bajo_critico": "chip fuera",
        "sin_datos": "chip cerca",
    }
    textos = {
        "dentro_de_banda": "dentro de banda normal",
        "cerca_del_minimo": "cerca de la cota mínima",
        "cerca_del_maximo": "cerca de la cota máxima",
        "bajo_minimo": "bajo la cota mínima",
        "sobre_maximo": "sobre la cota máxima",
        "bajo_critico": "bajo el nivel crítico",
        "sin_datos": "sin datos",
    }
    chips = []
    for embalse in estado["embalses"]:
        principal = embalse["estados"][0]
        cota = f"{embalse['cota_msnm']:.2f} msnm" if "cota_msnm" in embalse else "—"
        chips.append(
            f'<span class="{clases.get(principal, "chip cerca")}">'
            f"<strong>{_esc(embalse['embalse'])}</strong> {cota} · {textos.get(principal, principal)}</span>"
        )
    return "\n      ".join(chips)


def tabla_episodios(df: pd.DataFrame) -> str:
    """Episodios medidos: rachas ≥3 días bajo mínima, bajo crítica o sobre máxima."""
    filas = []
    for embalse, conf in EMBALSES.items():
        serie = (
            df[df["embalse"] == embalse]
            .set_index("fecha")["cota_msnm"]
            .asfreq("D")
            .dropna()
        )
        if serie.empty:
            continue

        def clasifica(cota: float) -> str | None:
            if conf["cota_min"] is not None and cota < conf["cota_min"]:
                return "bajo la cota mínima"
            if conf.get("cota_critica") is not None and cota < conf["cota_critica"]:
                return "bajo el nivel crítico"
            if conf["cota_max"] is not None and cota > conf["cota_max"]:
                return "sobre la cota máxima"
            return None

        clases = serie.map(clasifica)
        grupo = (clases != clases.shift()).cumsum()
        for _, indices in clases.groupby(grupo).groups.items():
            seg = clases.loc[indices]
            tipo = seg.iloc[0]
            if tipo is None or len(seg) < 3:
                continue
            valores = serie.loc[seg.index]
            filas.append(
                "<tr>"
                f"<th>{_esc(embalse)}</th><td>{_esc(tipo)}</td>"
                f"<td>{seg.index.min().strftime('%Y-%m-%d')}</td>"
                f"<td>{seg.index.max().strftime('%Y-%m-%d')}</td>"
                f"<td>{len(seg)}</td><td>{valores.min():.2f}</td></tr>"
            )
    if not filas:
        return "<p class='actualizado'>Sin episodios medidos de al menos 3 días consecutivos en la serie disponible.</p>"
    filas.sort(key=lambda f: f.split("<td>")[2])  # ordenar por fecha de inicio
    return (
        "<table><thead><tr><th>Embalse</th><th>Condición medida</th><th>Inicio</th>"
        "<th>Fin</th><th>Días</th><th>Cota mínima del episodio</th></tr></thead>"
        f"<tbody>{''.join(filas)}</tbody></table>"
    )


def seccion_generacion() -> str:
    """Composición de generación nacional según el tablero de CENACE (si hay datos)."""
    if not ARCHIVO_GENERACION.exists():
        return ""
    generacion = pd.read_csv(ARCHIVO_GENERACION)
    fila = generacion[generacion["periodo"] == "dia"].sort_values("fecha_consulta").iloc[-1]
    porcentajes = [
        ("Hidroeléctrica", fila["hidroelectrica_pct"]),
        ("Térmica", fila["termica_pct"]),
        ("Renovable", fila["renovable_pct"]),
        ("Importación", fila["importacion_pct"]),
        ("Exportación", fila["exportacion_pct"]),
    ]
    barras = "".join(
        f"<tr><th>{_esc(nombre)}</th><td>{valor:.2f}%</td></tr>" for nombre, valor in porcentajes
    )
    plantas = "".join(
        f"<tr><th>{_esc(nombre)}</th><td>{fila[f'{clave}_tablero']:.0f}</td></tr>"
        for nombre, clave in (("Mazar", "mazar"), ("Paute (Molino)", "paute"), ("Sopladora", "sopladora"))
    )
    return f"""
  <section>
    <h2>Contexto de generación eléctrica nacional (CENACE)</h2>
    <p>Composición porcentual del día según el <a href="https://www.cenace.gob.ec/info-operativa/InformacionOperativa.htm" target="_blank" rel="noopener">tablero de Información Operativa de CENACE</a>,
    recolectada diariamente. La caída de la participación hidroeléctrica frente a la térmica es el
    contexto eléctrico inmediato de unas cotas descendentes.</p>
    <div class="rejilla">
      <table><thead><tr><th colspan="2">Composición del día</th></tr></thead><tbody>{barras}</tbody></table>
      <table><thead><tr><th colspan="2">Cascada del Paute (valor del tablero)</th></tr></thead><tbody>{plantas}</tbody></table>
    </div>
    <p class="actualizado">Transparencia: las magnitudes absolutas del tablero de CENACE no cuadran con la
    demanda conocida del SNI, por lo que se publica la composición porcentual (invariante ante la unidad);
    los valores brutos quedan en <a href="datos/generacion_cenace.csv">generacion_cenace.csv</a> tal como
    los publica la fuente, pendientes de calibración contra informes oficiales. Consulta: {fila['fecha_consulta']}.</p>
  </section>"""


def enlaces_factsheets() -> str:
    paginas = sorted(DIR_FACTSHEETS.glob("*.html")) if DIR_FACTSHEETS.exists() else []
    if not paginas:
        return ""
    ultimo = paginas[-1]
    anteriores = "".join(
        f'<li><a href="factsheets/{p.name}">{p.stem}</a></li>' for p in paginas[:-1]
    )
    return f"""
  <section>
    <h2>Factsheets trimestrales</h2>
    <p>Hechos medidos por trimestre (cota inicio/fin, mínimos, máximos, días fuera de banda y bajo
    nivel crítico), listos para imprimir o citar:</p>
    <p><a class="boton" href="factsheets/{ultimo.name}">➤ Factsheet más reciente: {ultimo.stem}</a></p>
    <details><summary>Trimestres anteriores ({len(paginas) - 1})</summary><ul>{anteriores}</ul></details>
  </section>"""


def generar() -> Path:
    from datetime import datetime

    try:
        from zoneinfo import ZoneInfo

        zona = ZoneInfo(ZONA_HORARIA_ECUADOR)
    except Exception:  # pragma: no cover
        from datetime import timezone

        zona = timezone.utc
    actualizado = datetime.now(zona).strftime("%Y-%m-%d %H:%M (hora Ecuador)")

    df = cargar_datos()

    # estado legible por máquinas (docs/estado.json)
    from alertas import escribir_estado

    escribir_estado()

    # preparar carpetas del artefacto de publicación
    for carpeta in (DIR_SITIO, DIR_SITIO_FIGURAS, DIR_SITIO_DATOS):
        carpeta.mkdir(parents=True, exist_ok=True)
    for figura in DIR_FIGURAS.glob("*.png"):
        shutil.copy2(figura, DIR_SITIO_FIGURAS / figura.name)
    shutil.copy2(ARCHIVO_COTAS_RAW, DIR_SITIO_DATOS / "cotas_historico.csv")
    if ARCHIVO_COTAS_PROCESADAS.exists():
        shutil.copy2(ARCHIVO_COTAS_PROCESADAS, DIR_SITIO_DATOS / "cotas_diarias.csv")
    if ARCHIVO_GENERACION.exists():
        shutil.copy2(ARCHIVO_GENERACION, DIR_SITIO_DATOS / "generacion_cenace.csv")

    tarjetas = "\n".join(
        tarjeta_embalse(embalse, df[df["embalse"] == embalse].iloc[-1]) for embalse in EMBALSES
    )
    n_mediciones = len(df)
    rango = f"{df['fecha'].min().strftime('%Y-%m-%d')} → {df['fecha'].max().strftime('%Y-%m-%d')}"

    paginas_figuras = "\n".join(
        f"""
      <figure>
        <img src="figuras/{figura.name}" alt="{_esc(figura.stem.replace('_', ' '))}" loading="lazy">
        <figcaption>{_esc(figura.stem.replace('_', ' '))}</figcaption>
      </figure>"""
        for figura in sorted(DIR_FIGURAS.glob("*.png"))
    )

    documento = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cotas de embalses hidroeléctricos del Ecuador · Monitoreo ciudadano</title>
<style>
  :root {{ --tinta:#1a2332; --suave:#5a6b82; --linea:#dde3ec; --fondo:#f7f9fc; --acento:#1565c0; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:Georgia,'Times New Roman',serif; color:var(--tinta); background:var(--fondo); line-height:1.6; }}
  header {{ background:#10233f; color:#fff; padding:2.2rem 1.5rem; }}
  header h1 {{ margin:0 0 .4rem; font-size:1.6rem; font-weight:600; }}
  header p {{ margin:.2rem 0; color:#c6d4e6; max-width:60rem; }}
  main {{ max-width:60rem; margin:0 auto; padding:1.5rem; }}
  section {{ background:#fff; border:1px solid var(--linea); border-radius:8px; padding:1.4rem; margin:1.4rem 0; }}
  h2 {{ font-size:1.15rem; border-bottom:1px solid var(--linea); padding-bottom:.4rem; }}
  .principio {{ border-left:4px solid var(--acento); padding:.6rem 1rem; color:var(--suave); font-style:italic; }}
  .rejilla {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(16rem,1fr)); gap:1rem; }}
  .tarjeta {{ border:1px solid var(--linea); border-radius:8px; padding:1rem; }}
  .tarjeta h3 {{ margin:0 0 .3rem; }}
  .cota {{ font-size:2rem; margin:.2rem 0; color:var(--acento); font-family:Consolas,monospace; }}
  .unidad {{ font-size:1rem; color:var(--suave); }}
  .fecha-lectura, .detalle {{ color:var(--suave); font-size:.85rem; margin:.2rem 0; }}
  .tarjeta-estado {{ font-size:.85rem; margin:.4rem 0 .2rem; padding:.25rem .6rem; border-radius:1rem; display:inline-block; }}
  .tarjeta-estado.ok {{ background:#e3efe4; color:#1b5e20; }}
  .tarjeta-estado.fuera {{ background:#fdecea; color:#b71c1c; }}
  table {{ border-collapse:collapse; width:100%; font-size:.85rem; }}
  th, td {{ border:1px solid var(--linea); padding:.35rem .5rem; text-align:center; }}
  thead th {{ background:#eef2f8; }}
  figure {{ margin:1.2rem 0; text-align:center; }}
  figure img {{ max-width:100%; border:1px solid var(--linea); border-radius:6px; }}
  figcaption {{ color:var(--suave); font-size:.8rem; margin-top:.3rem; }}
  a {{ color:var(--acento); }}
  footer {{ text-align:center; color:var(--suave); font-size:.8rem; padding:1.5rem; }}
  .actualizado {{ color:var(--suave); font-size:.85rem; }}
  .rejilla-chips {{ display:flex; flex-wrap:wrap; gap:.6rem; }}
  .chip {{ border-radius:1rem; padding:.35rem .8rem; font-size:.85rem; border:1px solid var(--linea); background:#fff; }}
  .chip.ok {{ background:#e3efe4; color:#1b5e20; border-color:#c3dfc5; }}
  .chip.cerca {{ background:#fdf3dc; color:#8d6e00; border-color:#f0dfae; }}
  .chip.fuera {{ background:#fdecea; color:#b71c1c; border-color:#f3c1bd; }}
  .boton {{ display:inline-block; background:var(--acento); color:#fff; text-decoration:none;
           padding:.55rem 1rem; border-radius:6px; font-size:.9rem; }}
  details summary {{ cursor:pointer; color:var(--acento); margin:.4rem 0; }}
</style>
</head>
<body>
<header>
  <h1>Cotas de embalses hidroeléctricos del Ecuador</h1>
  <p>Monitoreo ciudadano, objetivo y reproducible de los embalses Mazar, Amaluza y Sopladora
     (cascada del río Paute, CELEC SUR) frente a sus umbrales operativos de referencia.</p>
  <p class="actualizado">Última actualización: {_esc(actualizado)} · {n_mediciones} mediciones diarias · serie {_esc(rango)}</p>
</header>
<main>
  <section>
    <h2>Principio del proyecto</h2>
    <p class="principio">Este sitio no afirma que exista desinformación. Superpone en una misma línea de
    tiempo verificable lo que dicen los sensores oficiales y lo que se comunicó oficialmente;
    las conclusiones pertenecen al lector.</p>
    <p>Fuente primaria: la misma API pública que alimenta el <a href="{_esc(URL_TABLERO_PUBLICO)}" target="_blank" rel="noopener">tablero
    oficial de Gráficas de Producción de CELEC SUR</a>. Método, umbrales y limitaciones completas en el
    repositorio (README y notebooks CRISP-DM).</p>
  </section>

  <section>
    <h2>Estado actual (banderas factuales)</h2>
    <p class="rejilla-chips">
      {banner_estado()}
    </p>
    <p class="actualizado">Banderas calculadas contra los umbrales declarados (margen de cercanía: 2 m).
    Versión legible por máquinas: <a href="estado.json">estado.json</a> — consumible por cualquier
    sistema de monitoreo o bot institucional.</p>
  </section>

  <section>
    <h2>Lectura más reciente por embalse</h2>
    <div class="rejilla">{tarjetas}
    </div>
  </section>

  <section>
    <h2>Series históricas frente a umbrales</h2>
    {paginas_figuras}
  </section>

  <section>
    <h2>Contexto trimestral (cota media / mínima / máxima, msnm)</h2>
    {tabla_trimestral(df)}
    <p class="actualizado">Resumen descriptivo por trimestre; no incorpora juicios operativos.</p>
  </section>

  <section>
    <h2>Episodios medidos fuera de banda o bajo nivel crítico</h2>
    <p>Rachas de al menos 3 días consecutivos con la cota por debajo de la mínima, por debajo del
    nivel crítico (Mazar) o por encima de la máxima declaradas. Generada desde el dato; sin
    redacción interpretativa.</p>
    {tabla_episodios(df)}
  </section>

  {seccion_generacion()}
  {enlaces_factsheets()}

  <section>
    <h2>Datos abiertos</h2>
    <ul>
      <li><a href="datos/cotas_historico.csv">cotas_historico.csv</a> — serie cruda auditable
          (fecha_consulta + mrid por fila)</li>
      <li><a href="datos/cotas_diarias.csv">cotas_diarias.csv</a> — tabla analítica con indicadores derivados</li>
    </ul>
    <p class="actualizado">El registro de comunicados oficiales y su cruce con cotas se mantienen en el repositorio
    (data/comunicados/ y notebooks 03–04).</p>
  </section>
</main>
<footer>
  Datos: CELEC SUR (fuente pública oficial) · Código: licencia MIT ·
  Los datos se presentan; las conclusiones son del lector.
</footer>
</body>
</html>
"""
    ruta_salida = DIR_SITIO / "index.html"
    ruta_salida.write_text(documento, encoding="utf-8")
    return ruta_salida


if __name__ == "__main__":
    ruta = generar()
    print("sitio →", ruta)
