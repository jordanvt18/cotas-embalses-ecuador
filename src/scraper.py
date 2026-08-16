# -*- coding: utf-8 -*-
"""
Scraper de cotas de embalses hidroeléctricos del Ecuador (CELEC SUR).

Recoge los niveles (cotas, en msnm) de los embalses Mazar, Amaluza y
Sopladora desde la misma API pública que alimenta el tablero oficial
"Gráficas de Producción" de CELEC SUR:

    https://generacioncsr.celec.gob.ec/graficasproduccion/

La API es un Oracle ORDS sin autenticación, publicado por la propia
empresa pública en su tablero web. robots.txt de celec.gob.ec no restringe
este acceso (ver README, sección de cumplimiento ético).

Modos de uso:
    python src/scraper.py diario      # día actual/mes actual (para GitHub Actions)
    python src/scraper.py backfill    # historia completa desde FECHA_INICIO_BACKFILL
    python src/scraper.py backfill --desde 2024-01-01

Salida: data/raw/cotas_historico.csv con columnas
    fecha_consulta (UTC), embalse, fecha (local Ecuador), cota_msnm, mrid

Además, en modo diario intenta archivar en web.archive.org (Save Page Now)
las URLs consultadas, dejando constancia inmutable del dato del día.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
import urllib3

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constantes import (  # noqa: E402
    ARCHIVO_COTAS_RAW,
    ARCHIVO_REGISTRO_ARCHIVO_WEB,
    EMBALSES,
    ENDPOINT_DIARIO,
    ENDPOINT_MENSUAL_H24,
    FECHA_INICIO_BACKFILL,
    PAUSA_ENTRE_LLAMADAS,
    URL_SAVE_PAGE_NOW,
    URL_TABLERO_PUBLICO,
    ZONA_HORARIA_ECUADOR,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
registro = logging.getLogger("scraper")

SESION = requests.Session()
SESION.headers.update({"Accept": "application/json", "User-Agent": "cotas-embalses-ecuador/1.0 (monitoreo ciudadano de datos públicos)"})


# ---------------------------------------------------------------------------
# Utilidades de fecha
# ---------------------------------------------------------------------------
try:  # Python >= 3.9 con zoneinfo
    from zoneinfo import ZoneInfo
    TZ_ECUADOR = ZoneInfo(ZONA_HORARIA_ECUADOR)
except Exception:  # pragma: no cover - fallback improbable
    TZ_ECUADOR = timezone.utc


def ahora_ecuador() -> datetime:
    return datetime.now(TZ_ECUADOR)


def fecha_iso_local(fecha: datetime) -> str:
    """Fecha local Ecuador en formato YYYY-MM-DD."""
    return fecha.astimezone(TZ_ECUADOR).strftime("%Y-%m-%d")


def meses_entre(desde: str, hasta: str):
    """Itera el primer día de cada mes entre dos fechas 'YYYY-MM-DD'."""
    anio, mes = int(desde[:4]), int(desde[5:7])
    anio_fin, mes_fin = int(hasta[:4]), int(hasta[5:7])
    while (anio, mes) <= (anio_fin, mes_fin):
        yield f"{anio:04d}-{mes:02d}-01"
        mes += 1
        if mes == 13:
            mes = 1
            anio += 1


# ---------------------------------------------------------------------------
# Acceso a la API oficial CELEC SUR
# ---------------------------------------------------------------------------
def _llamar_api(endpoint: str, mrid: int, fecha_inicio: str, fecha_fin: str) -> list[dict]:
    """Llama al endpoint ORDS y devuelve la lista de items.

    Formato de fechas exigido por el servidor (descubierto empíricamente):
    fechaInicio/fechaFin como ISO-8601 UTC con milisegundos y 'Z'
    (equivalente a Date.toJSON() en JavaScript, que es lo que envía el
    tablero oficial). El parámetro 'fecha' va como 'dd/MM/yyyy HH:mm:ss'.
    """
    parametros = {
        "mrid": mrid,
        "fechaInicio": f"{fecha_inicio}T00:00:00.000Z",
        "fechaFin": f"{fecha_fin}T00:00:00.000Z",
        "fecha": f"{fecha_inicio[8:10]}/{fecha_inicio[5:7]}/{fecha_inicio[:4]} 00:00:00",
    }
    respuesta = SESION.get(endpoint, params=parametros, verify=False, timeout=30)
    respuesta.raise_for_status()
    datos = respuesta.json()
    return datos.get("items", [])


def _fecha_local_desde_loctimestamp(loctimestamp: str) -> str:
    """Convierte '2026-07-31T05:00:00Z' (UTC) a fecha local Ecuador.

    05:00 UTC == 00:00 en America/Guayaquil (UTC-5): los valores diarios
    del endpoint MesH24 corresponden a la medianoche local del embalse.
    """
    return fecha_iso_local(datetime.fromisoformat(loctimestamp.replace("Z", "+00:00")))


def cota_diaria_del_mes(mes_inicio: str, embalse: str) -> list[dict]:
    """Serie diaria (cota a medianoche local) de un mes para un embalse."""
    conf = EMBALSES[embalse]
    anio, mes = int(mes_inicio[:4]), int(mes_inicio[5:7])
    # último día del mes
    mes_siguiente = f"{anio + (mes == 12):04d}-{(mes % 12) + 1:02d}-01"
    items = _llamar_api(ENDPOINT_MENSUAL_H24, conf["mrid_cota"], mes_inicio, mes_siguiente)
    filas = []
    for item in items:
        valor = item.get("valueedit")
        if valor is None:
            continue
        filas.append(
            {
                "embalse": embalse,
                "fecha": _fecha_local_desde_loctimestamp(item["loctimestamp"]),
                "cota_msnm": round(float(valor), 2),
                "mrid": conf["mrid_cota"],
            }
        )
    return filas


def ultima_cota_del_dia(fecha_local: str, embalse: str) -> dict | None:
    """Último valor horario disponible del día local indicado (endpoint diario)."""
    conf = EMBALSES[embalse]
    # el día local de Ecuador en UTC corre de 05:00Z del día D a 05:00Z del día D+1;
    # el endpoint acepta fechas a medianoche, pedimos el día D completo
    items = _llamar_api(ENDPOINT_DIARIO, conf["mrid_cota"], fecha_local, _dia_siguiente(fecha_local))
    con_valor = [i for i in items if i.get("valueedit") is not None]
    if not con_valor:
        return None
    ultimo = con_valor[0]  # el ORDS devuelve el más reciente primero
    return {
        "embalse": embalse,
        "fecha": fecha_local,
        "cota_msnm": round(float(ultimo["valueedit"]), 2),
        "mrid": conf["mrid_cota"],
    }


def _dia_siguiente(fecha: str) -> str:
    from datetime import date, timedelta

    d = date.fromisoformat(fecha)
    return (d + timedelta(days=1)).isoformat()


# ---------------------------------------------------------------------------
# Archivo web (web.archive.org, Save Page Now) — mejor esfuerzo
#
# El SPN anónimo devuelve 401 desde 2024; para archivar de forma fiable hay
# que crear claves gratuitas en https://archive.org/account/s3.php y definirlas
# en las variables de entorno ARCHIVE_S3_ACCESS y ARCHIVE_S3_SECRET
# (en GitHub Actions: secrets del repositorio). Sin claves, se intenta el
# acceso anónimo y el resultado —éxito o fallo— queda en el log.
# ---------------------------------------------------------------------------
def archivar_url(url: str) -> str | None:
    """Intenta guardar la URL en web.archive.org y devuelve el enlace al snapshot.

    Si falla (sin credenciales, sin conexión, rate-limit, etc.) devuelve None
    y se registra en el log; nunca interrumpe la recolección de datos.
    """
    import os

    acceso = os.environ.get("ARCHIVE_S3_ACCESS")
    secreto = os.environ.get("ARCHIVE_S3_SECRET")
    momento = datetime.now(timezone.utc).isoformat()
    try:
        if acceso and secreto:
            respuesta = SESION.post(
                f"{URL_SAVE_PAGE_NOW}{url}",
                headers={
                    "Accept": "application/json",
                    "Authorization": f"LOW {acceso}:{secreto}",
                },
                timeout=60,
                allow_redirects=True,
            )
        else:
            respuesta = SESION.get(f"{URL_SAVE_PAGE_NOW}{url}", timeout=45, allow_redirects=True)
        if respuesta.ok:
            snapshot = respuesta.url
            _registrar_archivo(f"{momento}\tOK\t{url}\t{snapshot}\n")
            return snapshot
        _registrar_archivo(f"{momento}\tHTTP_{respuesta.status_code}\t{url}\t\n")
    except Exception as error:  # noqa: BLE001
        _registrar_archivo(f"{momento}\tERROR\t{url}\t{error}\n")
    return None


def _registrar_archivo(linea: str) -> None:
    with open(ARCHIVO_REGISTRO_ARCHIVO_WEB, "a", encoding="utf-8") as manejador:
        manejador.write(linea)


# ---------------------------------------------------------------------------
# Persistencia del CSV consolidado
# ---------------------------------------------------------------------------
def guardar_filas(filas: list[dict]) -> None:
    """Añade filas al CSV histórico, deduplicando por (embalse, fecha)."""
    import pandas as pd

    nuevas = pd.DataFrame(filas)
    nuevas["fecha_consulta"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if ARCHIVO_COTAS_RAW.exists():
        historico = pd.read_csv(ARCHIVO_COTAS_RAW, dtype={"fecha": str})
        combinado = pd.concat([historico, nuevas], ignore_index=True)
    else:
        combinado = nuevas
    # gana la lectura más reciente en duplicados
    combinado = (
        combinado.sort_values("fecha_consulta")
        .drop_duplicates(subset=["embalse", "fecha"], keep="last")
        .sort_values(["embalse", "fecha"])
    )
    combinado.to_csv(ARCHIVO_COTAS_RAW, index=False, encoding="utf-8")
    registro.info("Guardadas %d filas → %s (total %d)", len(filas), ARCHIVO_COTAS_RAW, len(combinado))


# ---------------------------------------------------------------------------
# Modos de ejecución
# ---------------------------------------------------------------------------
def modo_diario() -> None:
    """Recolecta el mes en curso para los tres embalses y archiva evidencia."""
    hoy_local = fecha_iso_local(ahora_ecuador())
    mes_actual = f"{hoy_local[:7]}-01"
    filas = []
    for embalse in EMBALSES:
        try:
            obtenidas = cota_diaria_del_mes(mes_actual, embalse)
            filas.extend(obtenidas)
            registro.info("%s: %d cotas del mes %s", embalse, len(obtenidas), mes_actual)
        except Exception as error:  # noqa: BLE001
            registro.error("Fallo recolectando %s: %s", embalse, error)
        time.sleep(PAUSA_ENTRE_LLAMADAS)
    if filas:
        guardar_filas(filas)
    # Evidencia inmutable del día (mejor esfuerzo)
    registro.info("Archivando evidencia en web.archive.org (mejor esfuerzo)…")
    archivar_url(URL_TABLERO_PUBLICO)
    for embalse, conf in EMBALSES.items():
        url_api = (
            f"{ENDPOINT_MENSUAL_H24}?mrid={conf['mrid_cota']}"
            f"&fechaInicio={mes_actual}T00:00:00.000Z"
            f"&fechaFin={_dia_siguiente(mes_actual)}T00:00:00.000Z"
        )
        archivar_url(url_api)
        time.sleep(2)  # pausa por cortesía con Save Page Now


def modo_backfill(desde: str) -> None:
    """Reconstruye la historia diaria completa desde la fecha indicada."""
    hoy_local = fecha_iso_local(ahora_ecuador())
    registro.info("Backfill de cotas desde %s hasta %s", desde, hoy_local)
    for mes_inicio in meses_entre(desde, hoy_local):
        for embalse in EMBALSES:
            try:
                filas = cota_diaria_del_mes(mes_inicio, embalse)
                if filas:
                    guardar_filas(filas)
            except Exception as error:  # noqa: BLE001
                registro.error("Fallo en %s/%s: %s", embalse, mes_inicio, error)
            time.sleep(PAUSA_ENTRE_LLAMADAS)


def main() -> None:
    analizador = argparse.ArgumentParser(description="Scraper de cotas CELEC SUR")
    analizador.add_argument("modo", choices=["diario", "backfill"])
    analizador.add_argument("--desde", default=FECHA_INICIO_BACKFILL, help="fecha inicial YYYY-MM-DD para backfill")
    argumentos = analizador.parse_args()

    if argumentos.modo == "diario":
        modo_diario()
    else:
        modo_backfill(argumentos.desde)


if __name__ == "__main__":
    main()
