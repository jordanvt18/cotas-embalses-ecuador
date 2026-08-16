# -*- coding: utf-8 -*-
"""
Estado operativo de los embalses en formato legible por terceros.

Evalúa la última lectura de cada embalse contra sus umbrales declarados y
produce un JSON con banderas puramente factuales (sin lenguaje valorativo):

    docs/estado.json

Ese archivo se publica con el sitio (GitHub Pages) y puede consumirse desde
cualquier sistema de monitoreo, bot o tablero institucional:

    https://<usuario>.github.io/cotas-embalses-ecuador/estado.json

Banderas posibles por embalse (campo `estados`, lista):
    dentro_de_banda     — cota entre mínima y máxima declaradas
    bajo_minimo         — cota por debajo de la mínima declarada
    sobre_maximo        — cota por encima de la máxima declarada
    bajo_critico        — cota por debajo de la crítica declarada (Mazar)
    cerca_del_minimo    — a MARGEN_CERCANIA_M metros o menos de la mínima
    cerca_del_maximo    — a MARGEN_CERCANIA_M metros o menos de la máxima

Uso:
    python src/alertas.py            # evalúa y escribe docs/estado.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constantes import (  # noqa: E402
    ARCHIVO_COTAS_RAW,
    EMBALSES,
    MARGEN_CERCANIA_M,
    RAIZ,
    URL_TABLERO_PUBLICO,
    ZONA_HORARIA_ECUADOR,
)

ARCHIVO_ESTADO = RAIZ / "docs" / "estado.json"


def _ahora_ecuador_iso() -> str:
    from datetime import datetime

    try:
        from zoneinfo import ZoneInfo

        zona = ZoneInfo(ZONA_HORARIA_ECUADOR)
    except Exception:  # pragma: no cover
        from datetime import timezone

        zona = timezone.utc
    return datetime.now(zona).isoformat(timespec="seconds")


def evaluar_estado(df: pd.DataFrame | None = None) -> dict:
    """Evalúa la última lectura de cada embalse contra sus umbrales.

    Devuelve un dict serializable; no lanza si un embalse carece de datos.
    """
    if df is None:
        df = pd.read_csv(ARCHIVO_COTAS_RAW, parse_dates=["fecha"])

    embalses = []
    for nombre, conf in EMBALSES.items():
        grupo = df[df["embalse"] == nombre].sort_values("fecha")
        if grupo.empty:
            embalses.append({"embalse": nombre, "estados": ["sin_datos"]})
            continue
        fila = grupo.iloc[-1]
        cota = float(fila["cota_msnm"])
        estados = []
        if conf["cota_min"] is not None:
            if cota < conf["cota_min"]:
                estados.append("bajo_minimo")
            elif cota - conf["cota_min"] <= MARGEN_CERCANIA_M:
                estados.append("cerca_del_minimo")
        if conf["cota_max"] is not None:
            if cota > conf["cota_max"]:
                estados.append("sobre_maximo")
            elif conf["cota_max"] - cota <= MARGEN_CERCANIA_M:
                estados.append("cerca_del_maximo")
        if conf.get("cota_critica") is not None and cota < conf["cota_critica"]:
            estados.append("bajo_critico")
        if not estados:
            estados.append("dentro_de_banda")

        embalse = {
            "embalse": nombre,
            "fecha_lectura": fila["fecha"].strftime("%Y-%m-%d"),
            "cota_msnm": round(cota, 2),
            "estados": estados,
            "umbrales_msnm": {
                k: conf[k]
                for k in ("cota_min", "cota_critica", "cota_max")
                if conf.get(k) is not None
            },
            "distancias_m": {
                "a_minimo": round(cota - conf["cota_min"], 2),
                "a_maximo": round(conf["cota_max"] - cota, 2),
            },
            "mrid": int(fila["mrid"]),
            "fuente": URL_TABLERO_PUBLICO,
        }
        if conf.get("cota_critica") is not None:
            embalse["distancias_m"]["a_critico"] = round(cota - conf["cota_critica"], 2)
        embalses.append(embalse)

    return {
        "proyecto": "cotas-embalses-ecuador",
        "principio": "Banderas factuales contra umbrales declarados; sin valoraciones.",
        "generado_en": _ahora_ecuador_iso(),
        "zona_horaria": ZONA_HORARIA_ECUADOR,
        "margen_cercania_m": MARGEN_CERCANIA_M,
        "embalses": embalses,
        "endpoint_datos": "datos/cotas_historico.csv",
    }


def escribir_estado() -> Path:
    ARCHIVO_ESTADO.parent.mkdir(parents=True, exist_ok=True)
    estado = evaluar_estado()
    ARCHIVO_ESTADO.write_text(
        json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return ARCHIVO_ESTADO


if __name__ == "__main__":
    ruta = escribir_estado()
    print("estado →", ruta)
    for embalse in evaluar_estado()["embalses"]:
        print(f"  {embalse['embalse']}: {embalse.get('cota_msnm', '—')} {embalse['estados']}")
