# Registro de comunicados oficiales

Este directorio contiene el registro **manual y voluntario** de declaraciones
oficiales sobre el estado de los embalses hidroeléctricos, que el proyecto
contrastará con las cotas medidas.

## Esquema de `comunicados.csv`

| Columna | Descripción |
|---|---|
| `fecha` | Fecha de la declaración (YYYY-MM-DD, zona Ecuador) |
| `fuente` | Institución que emite la declaración (p. ej. CELEC SUR, Ministerio de Energía, CENACE, Presidencia) |
| `tipo` | `comunicado`, `rueda_de_prensa`, `entrevista`, `red_social_oficial`, `informe` |
| `enlace` | URL original donde se publicó |
| `enlace_archivo` | Snapshot en web.archive.org (opcional pero recomendado) |
| `mensaje_parafraseado` | Paráfrasis fiel y neutra del contenido relevante (sin citas textuales largas) |

## Reglas de registro

1. **Solo fuentes oficiales identificables**: instituciones públicas con nombre,
   cargo y fecha. No se registran rumores ni notas de prensa que citen a
   "fuentes anónimas".
2. **Paráfrasis, no citas**: se resume el mensaje en términos neutros.
   El enlace original permite verificar el texto exacto.
3. **Sin interpretación**: no se clasifica la declaración como
   "verdadera/falsa"; el contraste numérico con las cotas medidas lo hacen
   los notebooks, y el lector saca sus propias conclusiones.
4. **Se registran declaraciones de cualquier signo**: tanto las que afirman
   niveles bajos como altos, crisis o normalidad.
