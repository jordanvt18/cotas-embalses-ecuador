# Cotas de embalses hidroeléctricos del Ecuador · Monitoreo ciudadano de datos oficiales

[![Recolección diaria](https://github.com/jordanvt18/cotas-embalses-ecuador/actions/workflows/recoleccion_diaria.yml/badge.svg)](../../actions)
[![Sitio publicado](https://img.shields.io/badge/sitio-GitHub%20Pages-1565c0)](https://jordanvt18.github.io/cotas-embalses-ecuador/)

Monitoreo **objetivo, reproducible y automatizado** de las cotas (niveles, en
msnm) de los embalses **Mazar**, **Amaluza** y **Sopladora** — la cascada del
río Paute operada por CELEC SUR — presentadas contra sus umbrales operativos
de referencia y contra las fechas de comunicados oficiales.

> **Principio del proyecto:** este repositorio **no afirma** que exista
> desinformación. Su premisa es neutral: superponer en una misma línea de
> tiempo verificable *lo que dicen los sensores oficiales* y *lo que se
> comunicó oficialmente*, y dejar que cada lector saque sus propias
> conclusiones. Ningún gráfico ni tabla clasifica declaraciones como
> verdaderas o falsas.

---

## ¿Por qué este proyecto?

El estado de los embalses aparece en el debate público ecuatoriano cada vez
que hay riesgo de racionamiento, pero la ciudadanía rara vez tiene acceso a
la **serie histórica medida** de forma sencilla. El tablero público de CELEC
SUR muestra las últimas 24 horas o el mes en curso; no ofrece descarga masiva
ni archivo público de la serie diaria completa.

Este proyecto llena ese vacío recolectando **un dato diario por embalse**
desde la misma fuente oficial que alimenta el tablero, publicándolo en un
CSV versionado en git y respaldándolo (mejor esfuerzo) en web.archive.org.

## Estructura del repositorio

```
├── data/
│   ├── raw/
│   │   ├── cotas_historico.csv      # serie diaria cruda (auditada: fecha_consulta + mrid)
│   │   └── archivo_web.log          # intentos de respaldo en web.archive.org
│   ├── processed/
│   │   ├── cotas_diarias.csv        # tabla analítica (notebook 03)
│   │   └── comunicados_con_cota.csv # cruce comunicado ↔ cota medida
│   └── comunicados/
│       ├── comunicados.csv          # registro manual de declaraciones oficiales
│       └── LEEME.md                 # reglas de registro (neutras)
├── docs/                            # sitio estático de GitHub Pages (generado)
├── notebooks/                       # 5 fases CRISP-DM
│   ├── 01_comprension_negocio.ipynb
│   ├── 02_comprension_datos.ipynb
│   ├── 03_preparacion_datos.ipynb
│   ├── 04_modelado_visualizacion.ipynb
│   └── 05_evaluacion_conclusiones.ipynb
├── src/
│   ├── constantes.py                # umbrales oficiales, MRIDs, endpoints
│   ├── scraper.py                   # recolección (diaria / backfill)
│   ├── visualizacion.py             # figuras semáforo y cruces
│   └── generar_sitio.py             # genera docs/index.html para Pages
├── reports/figures/                 # PNG listos para publicar
├── .github/
│   ├── workflows/recoleccion_diaria.yml
│   └── dependabot.yml               # actualización semanal de acciones
├── SECURITY.md                      # política de seguridad y reporte
└── requirements.txt
```

## La fuente de datos (descubrimiento documentado)

El tablero oficial [Gráficas de Producción de CELEC SUR](https://generacioncsr.celec.gob.ec/graficasproduccion/)
es una aplicación Angular sin autenticación. Inspeccionando su código se
identificó el servicio REST que la alimenta — un **Oracle ORDS público**:

```
https://generacioncsr.celec.gob.ec:8443/ords/csr/sardomcsr/pointValues        # serie horaria
https://generacioncsr.celec.gob.ec:8443/ords/csr/sardomcsr/pointValuesMesH24  # serie diaria (cota a medianoche local)
```

**Puntos de medición validados** (los valores devueltos caen dentro de los
rangos operativos conocidos de cada embalse):

| Embalse | `mrid` cota | Validación (2026-08) |
|---|---|---|
| Mazar | 30031 | 2150.95 msnm ∈ [2098, 2153] ✓ |
| Amaluza | 24019 | 1985.12 msnm ∈ [1975, 1991] ✓ |
| Sopladora | 90919 | 1316.70 msnm ∈ [1312, 1318] ✓ |

El contrato completo de la API (formatos de fecha exigidos por el servidor,
estructura de respuesta, zona horaria) está documentado en el notebook
`02_comprension_datos.ipynb`.

> **Nota de transparencia:** el puerto 8443 sirve un certificado TLS
> autofirmado; el scraper desactiva la verificación de cadena (y lo declara
> aquí abiertamente). La integridad del dato se garantiza por triple vía:
> contraste con el tablero público, validación contra rangos operativos y
> respaldo en web.archive.org.

## Umbrales operativos de referencia

Declarados como constantes auditables en `src/constantes.py`:

| Embalse | Mínima | Crítica | Máxima |
|---|---|---|---|
| Mazar | 2098 | 2115 | 2153 |
| Amaluza | 1975 | — | 1991 |
| Sopladora | 1312 | — | 1318 |

Los títulos de las gráficas del propio tablero oficial muestran estos mismos
límites (p. ej. *"Cota Amaluza — min:1975 max:1991"*), lo que sirve de
verificación cruzada. Si la normativa cambia, se actualiza la constante y el
historial del commit registra el cambio.

## Uso

```bash
pip install -r requirements.txt

python src/scraper.py diario              # recolecta el mes en curso (lo que usa GitHub Actions)
python src/scraper.py backfill            # reconstruye la historia (desde 2022-01-01)
python src/scraper.py backfill --desde 2025-01-01
python src/visualizacion.py               # regenera las figuras de reports/figures/
python src/generar_sitio.py               # regenera el sitio de docs/ (GitHub Pages)
jupyter lab notebooks/                    # análisis CRISP-DM completo
```

## Automatización y sitio público

Un workflow de GitHub Actions corre a diario (12:00 UTC = 07:00 Ecuador):
ejecuta el scraper en modo diario, regenera las figuras y el sitio web, hace
commit del CSV actualizado y **publica el sitio en GitHub Pages**. Cada fila
del CSV lleva su `fecha_consulta` (UTC), de modo que la historia de git
permite auditoría completa: qué dato se obtuvo, cuándo y con qué versión del
código.

El sitio (`docs/index.html`, generado por `src/generar_sitio.py`) muestra la
lectura más reciente por embalse, las figuras semáforo, el contexto
trimestral y enlaces de descarga directa a los CSV. Es estático, sin
JavaScript y de contenido autogenerado.

**Activar GitHub Pages (una sola vez):** en el repositorio, ve a
*Settings → Pages → Source* y selecciona **GitHub Actions**. El primer
despliegue puede dispararse manualmente desde la pestaña *Actions* con
*Run workflow*. El sitio queda en
`https://jordanvt18.github.io/cotas-embalses-ecuador/`.

**Seguridad del pipeline** (detalles en `SECURITY.md`): permisos mínimos por
trabajo, checkout sin persistencia de credenciales donde no se hace push,
Dependabot semanal para las acciones, timeouts acotados y sin secretos en
logs.

**Respaldo en web.archive.org (opcional pero recomendado):** el *Save Page
Now* anónimo devuelve 401 desde 2024. Para que el archivado diario sea fiable,
crea claves gratuitas en [archive.org/account/s3.php](https://archive.org/account/s3.php)
y configúralas como *secrets* del repositorio: `ARCHIVE_S3_ACCESS` y
`ARCHIVE_S3_SECRET`. Sin ellas, cada intento anónimo y su resultado quedan
registrados en `data/raw/archivo_web.log`.

## Comunicados oficiales

`data/comunicados/comunicados.csv` es un registro **manual** de declaraciones
oficiales (CELEC, Ministerio de Energía, CENACE, Presidencia…) con esquema:
`fecha, fuente, tipo, enlace, enlace_archivo, mensaje_parafraseado`.

Reglas (detalladas en `data/comunicados/LEEME.md`): solo fuentes oficiales
identificables; paráfrasis neutra; se registran declaraciones **de cualquier
signo** (crisis o normalidad); sin clasificación de veracidad. El notebook 04
marca esas fechas sobre la serie y el notebook 03 produce la tabla
`comunicados_con_cota.csv` con la cota medida de cada día de declaración.

## Cumplimiento ético y legal

- **robots.txt:** celec.gob.ec y cenace.gob.ec usan el estándar WordPress que
  solo restringe `/wp-admin/`; el acceso general está permitido.
- **Carga del servidor:** 3 peticiones diarias (una por embalse) con pausas
  de cortesía; equivalente a un usuario humano consultando el tablero.
- **Datos públicos:** la API no requiere autenticación y alimenta una página
  pública; se usa la misma vía que cualquier navegador al visitar el tablero.
- **Sin scraping de terceros:** la verificación con prensa es un protocolo
  manual documentado (notebook 05); este scraper no toca medios privados.

## Limitaciones (extracto)

- La cota diaria corresponde a medianoche hora Ecuador; mínimos intradía no
  quedan capturados (el endpoint horario queda documentado para consultas).
- Serie disponible desde 2022-01-01 (límite verificado de la API).
- El respaldo en web.archive.org es mejor-esfuerzo; cada intento queda en
  `data/raw/archivo_web.log`.
- El registro de comunicados es manual: cobertura parcial por diseño.

La lista completa y sus mitigaciones están en `05_evaluacion_conclusiones.ipynb`.

## Estado del dataset

| Embalse | Serie | Mediciones |
|---|---|---|
| Mazar | 2022-01-01 → hoy | diaria |
| Amaluza | 2022-01-01 → hoy | diaria |
| Sopladora | 2022-01-01 → hoy | diaria |

## Licencia y uso

Datos: provienen de fuentes públicas oficiales (CELEC SUR). Código: MIT.
Si usas este material, cita la fuente original y este repositorio. Recuerda
el principio del proyecto: **los datos se presentan; las conclusiones son del lector.**
