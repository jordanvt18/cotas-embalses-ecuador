# Post de LinkedIn · cotas-embalses-ecuador

**Imagen adjunta:** `reports/figures/post_linkedin.png`
(generada por `src/post_linkedin.py` desde los datos reales)

---

## Texto para publicar (copiar y pegar)

En noviembre de 2024 Ecuador vivió apagones de hasta 14 horas. ¿Cómo estaba realmente el embalse Mazar ese mes?

Bajo su nivel crítico 24 de los 30 días.

Esa cifra no es una opinión: es un conteo sobre la cota diaria medida por el SCADA de CELEC SUR — datos públicos que casi nadie puede consultar en serie histórica, porque el tablero oficial solo muestra el día en curso.

Así que lo automatizé:

📊 Recolecto a diario (GitHub Actions) la cota de Mazar, Amaluza y Sopladora desde la misma API oficial que alimenta el tablero público de CELEC SUR. Serie: 2022 → hoy, ~4.900 mediciones, cada una auditable (fecha de consulta + identificador del punto de medición).

Lo que el dato ya documenta — y cualquiera puede verificar:

🔴 Mazar pasó 66 días bajo su nivel crítico en 2024: 24 en noviembre, 16 en octubre, 16 en abril, 10 en diciembre.
🟢 Hoy los tres embalses están dentro de banda, y Mazar a solo 2,35 m de su máximo (el dato también sirve para el riesgo opuesto: vertimiento).
📈 El deterioro de abril→octubre de 2024 era visible en la serie meses antes de la crisis.

Todo está abierto y listo para usar:

🌐 Sitio con series, episodios y contexto: jordanvt18.github.io/cotas-embalses-ecuador
🤖 estado.json — banderas factuales por embalse, consumible por cualquier sistema de monitoreo institucional
📄 Factsheets trimestrales imprimibles (2022-Q1 → hoy)
📥 CSV versionado en git, metodología CRISP-DM documentada

Una regla de diseño que me importa: el proyecto no afirma que hubo desinformación ni apunta a nadie. Superpone lo que dicen los sensores oficiales y lo que se comunicó oficialmente — las conclusiones son del lector. Creo que así se construye confianza en los datos públicos: con método, fuentes citadas y cero editorial.

Si trabajas en energía, regulación, prensa de datos o simplemente quieres verificar una declaración oficial sobre los embalses: los datos están ahí.

¿Qué otra variable pública monitorearías así?

#DataScience #Energía #Ecuador #Transparencia #OpenData #Python #GitHub

---

## Notas de publicación

- **Horario sugerido:** martes a jueves, 07:30–08:30 (Ecuador) — ventana de mayor actividad profesional.
- **Primer comentario (tuyo):** añade el enlace al repositorio
  https://github.com/jordanvt18/cotas-embalses-ecuador
  (LinkedIn da menos alcance a enlaces en el cuerpo del post; el del texto
  principal es la GitHub Pages, que no penaliza igual al ser contexto).
- **Engagement:** responde los comentarios con el factsheet del trimestre
  correspondiente cuando pregunten por datos concretos
  (p. ej. factsheets/2024-Q4.html para lo de noviembre).
- Los números citados son verificables: 66 días bajo crítico (16+24+16+10 en
  2024), 2,35 m bajo el máximo al 15-ago-2026, ~4.900 mediciones.
