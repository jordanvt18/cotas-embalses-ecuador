# Post de LinkedIn · cotas-embalses-ecuador (versión registro académico)

**Imagen adjunta:** `reports/figures/post_linkedin.png`
(generada por `src/post_linkedin.py` desde los datos reales)

---

## Texto para publicar (copiar y pegar)

En noviembre de 2024, durante la crisis de racionamiento eléctrico del Ecuador, el embalse Mazar permaneció bajo su nivel crítico declarado 24 de los 30 días del mes.

Esta afirmación no procede de ninguna fuente periodística: la obtuve contando los registros diarios que mide el SCADA de CELEC SUR. Son datos públicos, aunque de acceso efectivamente restringido, pues el tablero oficial solo exhibe la jornada en curso y no ofrece la serie histórica en formato descargable. Esa asimetría —entre la disponibilidad técnica del dato y su inaccesibilidad práctica— es el problema que decidí abordar.

Desarrollé, en consecuencia, un sistema de monitoreo ciudadano que reconstruye la serie diaria de cotas de los embalses Mazar, Amaluza y Sopladora a partir de la misma interfaz pública que alimenta el tablero oficial. El sistema opera de manera automatizada mediante GitHub Actions, acumula cerca de 4.900 mediciones desde enero de 2022 y conserva, para cada registro, la marca temporal de consulta y el identificador del punto de medición, de modo que cualquier persona puede auditar y reproducir la obtención del dato.

Tres hallazgos de la serie merecen señalarse:

Primero. Mazar permaneció 66 días bajo su nivel crítico a lo largo de 2024: 16 en abril, 16 en octubre, 24 en noviembre y 10 en diciembre. La severidad del episodio de noviembre es, por tanto, verificable con precisión diaria.

Segundo. La trayectoria de deterioro entre abril y octubre de 2024 era observable en la serie con meses de antelación respecto del racionamiento, lo que sugiere el valor de estas mediciones como insumo de gestión de riesgo, y no solo de constatación retrospectiva.

Tercero. A la fecha de hoy los tres embalses se encuentran dentro de sus bandas operativas normales, con Mazar a 2,35 metros bajo su cota máxima: el mismo instrumento permite constatar condiciones opuestas, como el riesgo de vertimiento.

He dispuesto todos los productos en acceso abierto: el sitio con las series y los episodios documentados (jordanvt18.github.io/cotas-embalses-ecuador), un archivo estado.json con banderas factuales por embalse que cualquier sistema institucional puede consumir, factsheets trimestrales imprimibles desde 2022-Q1, y los archivos CSV versionados en git con la metodología CRISP-DM documentada en su integridad.

Conviene explicitar el principio metodológico que sostiene el proyecto: no afirmo que haya existido desinformación, ni el trabajo señala a actor alguno. Me limito a superponer, en una misma línea de tiempo verificable, lo que registran los sensores oficiales y lo que se comunicó oficialmente. Sostengo que la confianza en los datos públicos se construye con método declarado, fuentes citadas y ausencia deliberada de editorial.

A quienes trabajan en energía, regulación, verificación de datos o investigación: el instrumento está disponible. Agradezco, desde ya, las observaciones metodológicas que la comunidad pueda formular.

¿Qué otra variable de interés público consideran que ameritaría un monitoreo de estas características?

#CienciaDeDatos #Energía #Ecuador #Transparencia #DatosAbiertos

---

## Notas de publicación

- **Horario sugerido:** martes a jueves, 07:30–08:30 (Ecuador).
- **Primer comentario (tuyo):** enlace al repositorio
  https://github.com/jordanvt18/cotas-embalses-ecuador
- **Tono:** mantener la respuesta a comentarios en el mismo registro: sobrio,
  con remisión a las fuentes (factsheets, CSV) ante cualquier observación.
- Los números citados son verificables: 66 días bajo crítico (16+24+16+10 en
  2024), 2,35 m bajo el máximo al 15-ago-2026, ~4.900 mediciones.
