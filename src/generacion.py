# -*- coding: utf-8 -*-
"""
Colector de contexto de generación eléctrica nacional (CENACE).

La página de Información Operativa de CENACE
(info-operativa/InformacionOperativa.htm) publica sus cifras como gráficos
Plotly embebidos en el HTML. Este módulo extrae, para tres periodos
(día en curso, mes en curso, año en curso):

  - la composición por fuente: hidroeléctrica, térmica, renovable,
    importación, exportación (valores tal como los publica el tablero);
  - la producción declarada de las plantas de la cascada del Paute:
    Mazar, Paute (Molino) y Sopladora.

TRANSPARENCIA SOBRE LAS MAGNITUDES: los valores absolutos del tablero no
coinciden con la demanda nacional conocida del SNI (implican ~300 MW de
promedio nacional), por lo que el análisis público del proyecto utiliza la
COMPOSICIÓN PORCENTUAL — invariante ante la unidad — y deja los valores
absolutos registrados tal cual, con la salvedad documentada en el README.
La composición relativa sí es consistente entre las pestañas diaria,
mensual y anual.

Salida: data/generacion/generacion_cenace.csv con una fila por
(fecha_consulta, periodo) y fecha_consulta en UTC.

Uso:
    python src/generacion.py
"""

from __future__ import annotations

import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
import urllib3

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constantes import (  # noqa: E402
    ARCHIVO_GENERACION,
    DIR_GENERACION,
    URL_INFO_OPERATIVA_CENACE,
    ZONA_HORARIA_ECUADOR,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
registro = logging.getLogger("generacion")

SESION = requests.Session()
SESION.headers.update(
    {"User-Agent": "cotas-embalses-ecuador/1.0 (monitoreo ciudadano de datos públicos)"}
)

# posición de los grupos de gráficos en la página (validada 2026-08):
# trozos 0-4 = producción en tiempo real (día), 6-9 = mensual, 10-13 = anual
INDICE_PIE_POR_GRUPO = {"dia": 0, "mes": 6, "anio": 10}

FUENTES = ("IMPORTACIÓN", "HIDROELÉCTRICA", "TÉRMICA", "RENOVABLE", "EXPORTACIÓN")
PLANTAS_PAUTE = ("Mazar", "Paute", "Sopladora")

_BARRA = "\\"


def _extraer_array(texto: str) -> list:
    """Extrae el primer array JSON balanceado de la cadena (datos Plotly)."""
    inicio = texto.find("[")
    nivel, en_cadena, escape = 0, False, False
    for i in range(inicio, len(texto)):
        c = texto[i]
        if en_cadena:
            if escape:
                escape = False
            elif c == _BARRA:
                escape = True
            elif c == '"':
                en_cadena = False
        else:
            if c == '"':
                en_cadena = True
            elif c == "[":
                nivel += 1
            elif c == "]":
                nivel -= 1
                if nivel == 0:
                    return json.loads(texto[inicio : i + 1])
    raise ValueError("array sin cierre")


def _obtener_html() -> str:
    try:
        respuesta = SESION.get(URL_INFO_OPERATIVA_CENACE, timeout=30)
        respuesta.raise_for_status()
        return respuesta.text
    except requests.exceptions.SSLError:
        registro.warning("TLS de CENACE falló con verificación estricta; reintento sin verificar cadena")
        respuesta = SESION.get(URL_INFO_OPERATIVA_CENACE, timeout=30, verify=False)
        respuesta.raise_for_status()
        return respuesta.text


def _sin_acentos(texto: str) -> str:
    import unicodedata

    return "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )


def _porcentaje(valor: float, total: float) -> float:
    return round(100.0 * valor / total, 2) if total else 0.0


def recolectar() -> list[dict]:
    """Devuelve las filas del día (una por periodo: dia/mes/anio)."""
    html = _obtener_html()
    trozos = re.split(r"Plotly\.newPlot\(", html)[1:]

    filas = []
    for periodo, indice_pie in INDICE_PIE_POR_GRUPO.items():
        try:
            # el pie del periodo y las barras por planta están en el gráfico siguiente
            trazas_pie = _extraer_array(trozos[indice_pie])
            trazas_plantas = _extraer_array(trozos[indice_pie + 1])
        except (IndexError, ValueError, json.JSONDecodeError) as error:
            registro.error("estructura del tablero CENACE cambió (%s, %s): %s", periodo, indice_pie, error)
            continue

        pie = next((t for t in trazas_pie if t.get("type") == "pie" and "labels" in t), None)
        if pie is None:
            registro.error("sin pie de composición en el grupo %s", periodo)
            continue
        composicion = {et: float(v) for et, v in zip(pie["labels"], pie["values"])}

        plantas = {}
        for traza in trazas_plantas:
            nombre = (traza.get("name") or "").strip()
            if nombre in PLANTAS_PAUTE:
                valores = traza.get("y", [])
                if valores and isinstance(valores[0], (int, float)):
                    plantas[nombre] = float(valores[0])

        # generación bruta nacional del tablero = suma de fuentes menos exportación
        bruto = sum(composicion.get(f, 0.0) for f in FUENTES) - composicion.get("EXPORTACIÓN", 0.0)

        fila = {
            "fecha_consulta": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "periodo": periodo,
        }
        for fuente in FUENTES:
            clave = _sin_acentos(fuente.lower())
            fila[f"{clave}_tablero"] = round(composicion.get(fuente, 0.0), 3)
            fila[f"{clave}_pct"] = _porcentaje(composicion.get(fuente, 0.0), bruto)
        fila["generacion_bruta_tablero"] = round(bruto, 3)
        fila["unidad_declarada"] = "según tablero CENACE (magnitud por validar contra informes oficiales)"
        for planta, valor in plantas.items():
            fila[f"{planta.lower()}_tablero"] = round(valor, 3)
        filas.append(fila)
        registro.info(
            "%s: hidráulica %.1f%% | térmica %.1f%% | Mazar/Paute/Sopladora capturadas: %s",
            periodo,
            fila.get("hidroelectrica_pct", 0),
            fila.get("termica_pct", 0),
            sorted(plantas),
        )
    return filas


def guardar(filas: list[dict]) -> None:
    import pandas as pd

    DIR_GENERACION.mkdir(parents=True, exist_ok=True)
    nuevas = pd.DataFrame(filas)
    if ARCHIVO_GENERACION.exists():
        historico = pd.read_csv(ARCHIVO_GENERACION)
        combinado = pd.concat([historico, nuevas], ignore_index=True)
    else:
        combinado = nuevas
    # deduplicar por fecha local del día de consulta + periodo
    combinado["fecha_local"] = (
        pd.to_datetime(combinado["fecha_consulta"], utc=True)
        .dt.tz_convert(ZONA_HORARIA_ECUADOR)
        .dt.strftime("%Y-%m-%d")
    )
    combinado = (
        combinado.sort_values("fecha_consulta")
        .drop_duplicates(subset=["fecha_local", "periodo"], keep="last")
        .drop(columns=["fecha_local"])
    )
    combinado.to_csv(ARCHIVO_GENERACION, index=False, encoding="utf-8")
    registro.info("guardado → %s (%d filas)", ARCHIVO_GENERACION, len(combinado))


def main() -> None:
    filas = recolectar()
    if filas:
        guardar(filas)
    else:
        registro.warning("sin filas recolectadas; no se modifica el histórico")


if __name__ == "__main__":
    main()
