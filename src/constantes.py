# -*- coding: utf-8 -*-
"""
Constantes del proyecto: umbrales operativos oficiales de embalses,
identificadores de la API de CELEC SUR y rutas de datos.

Los umbrales de cota (en msnm) provienen de la normativa operativa de
referencia declarada en el README (rangos mínimos/críticos/máximos por
embalse). No son estimaciones propias: son constantes de referencia
declaradas para poder contrastar los datos medidos contra ellas.

Fuentes de los rangos:
- Mazar:     cota mínima 2098, cota crítica 2115, cota máxima 2153 msnm
- Amaluza:   cota mínima 1975, cota máxima 1991 msnm
- Sopladora: rango normal 1312 – 1318 msnm
(Verificados además contra los títulos de las gráficas oficiales del
tablero CELEC SUR "Niveles y Caudales", que muestran "min:1975 max:1991"
para Amaluza y límites equivalentes para las demás centrales.)
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Rutas del repositorio
# ---------------------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent
DIR_RAW = RAIZ / "data" / "raw"
DIR_PROCESADOS = RAIZ / "data" / "processed"
DIR_COMUNICADOS = RAIZ / "data" / "comunicados"
DIR_FIGURAS = RAIZ / "reports" / "figures"

ARCHIVO_COTAS_RAW = DIR_RAW / "cotas_historico.csv"
ARCHIVO_COTAS_PROCESADAS = DIR_PROCESADOS / "cotas_diarias.csv"
ARCHIVO_COMUNICADOS = DIR_COMUNICADOS / "comunicados.csv"
ARCHIVO_REGISTRO_ARCHIVO_WEB = DIR_RAW / "archivo_web.log"

# ---------------------------------------------------------------------------
# API oficial CELEC SUR (Oracle ORDS tras el tablero público
# "Gráficas de Producción" → https://generacioncsr.celec.gob.ec/graficasproduccion/)
#
# El tablero es público y sin autenticación; esta API es el mismo servicio
# que consume el tablero oficial. El puerto 8443 sirve un certificado
# autofirmado, por lo que las peticiones se hacen con verificación TLS
# desactivada (se documenta en el README).
# ---------------------------------------------------------------------------
URL_BASE_ORDS = "https://generacioncsr.celec.gob.ec:8443/ords/csr/sardomcsr"
# Serie horaria (devuelve ~24 puntos del día indicado)
ENDPOINT_DIARIO = f"{URL_BASE_ORDS}/pointValues"
# Serie diaria: un valor por día (cota a medianoche hora Ecuador) del mes indicado
ENDPOINT_MENSUAL_H24 = f"{URL_BASE_ORDS}/pointValuesMesH24"

URL_TABLERO_PUBLICO = "https://generacioncsr.celec.gob.ec/graficasproduccion/"

# Zona horaria oficial del Ecuador continental (UTC-5, sin horario de verano)
ZONA_HORARIA_ECUADOR = "America/Guayaquil"

# Retardo (segundos) entre llamadas consecutivas a la API, por cortesía
PAUSA_ENTRE_LLAMADAS = 0.5

# ---------------------------------------------------------------------------
# Embalses monitorizados.
#
# mrid = identificador del punto medido en el SCADA de CELEC SUR,
# descubierto inspeccionando el código del tablero oficial y VALIDADO
# contrastando los valores devueltos con los rangos operativos conocidos
# (Mazar ~2150 msnm, Amaluza ~1985 msnm, Sopladora ~1316 msnm en agosto 2026).
# ---------------------------------------------------------------------------
EMBALSES = {
    "Mazar": {
        "mrid_cota": 30031,
        "mrid_caudal": 30538,
        "central": "Mazar",
        "rio": "Paute",
        "cota_min": 2098.0,
        "cota_critica": 2115.0,
        "cota_max": 2153.0,
    },
    "Amaluza": {
        "mrid_cota": 24019,
        "mrid_caudal": 24811,
        "central": "Molino (Amaluza)",
        "rio": "Paute",
        "cota_min": 1975.0,
        "cota_critica": None,   # la normativa publica rango min-max sin nivel crítico
        "cota_max": 1991.0,
    },
    "Sopladora": {
        "mrid_cota": 90919,
        "mrid_caudal": 90537,
        "central": "Sopladora",
        "rio": "Paute",
        "cota_min": 1312.0,
        "cota_critica": None,
        "cota_max": 1318.0,
    },
}

# Fecha inicial del backfill histórico (primer mes con datos verificado en la API)
FECHA_INICIO_BACKFILL = "2022-01-01"

# ---------------------------------------------------------------------------
# Web Archive (archive.org) — "Save Page Now"
# Se usa en modo mejor-esfuerzo: si el archivo falla, se registra en el log
# y la recolección continúa. Nunca interrumpe el pipeline.
# ---------------------------------------------------------------------------
URL_SAVE_PAGE_NOW = "https://web.archive.org/save/"
