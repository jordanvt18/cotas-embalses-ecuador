# Política de seguridad

## Alcance

Este repositorio publica: (a) código de recolección y visualización
(`src/`), (b) datos abiertos de origen público oficial (`data/`), (c) un
sitio estático generado (`docs/`) y (d) flujos de trabajo de GitHub Actions.

## Reporte de vulnerabilidades

Si encuentras una vulnerabilidad en el código o en la configuración del
CI, por favor repórtala de forma privada abriendo un
[*Security Advisory*](../../security/advisories/new) en este repositorio
(o contacta al mantenedor por el canal indicado en su perfil). Evita
abrir un issue público para material sensible.

## Prácticas aplicadas

- **Mínimos privilegios:** cada trabajo del workflow declara solo los
  permisos que usa (`contents: write` para el commit; `pages: write` e
  `id-token: write` únicamente en el despliegue de Pages, via entorno
  `github-pages`).
- **Sin credenciales en el repositorio:** las claves opcionales de
  archive.org se inyectan como *secrets* de GitHub y nunca se registran
  en logs (el log de archivado guarda URL y código HTTP, nada más).
- **Checkout sin persistencia** en los trabajos que no hacen push.
- **Timeouts y concurrencia acotados** para evitar ejecuciones huérfanas.
- **Dependabot** vigila las acciones del workflow semanalmente.
- **Superficie de red mínima:** el scraper solo contacta el dominio
  oficial de CELEC SUR y, en modo mejor esfuerzo, web.archive.org.
- **Sitio estático sin JavaScript ni contenidos de terceros**: el HTML
  publicado se genera de forma determinista desde los datos locales.

## Consideraciones conocidas y aceptadas

- La API de CELEC SUR sirve un certificado TLS autofirmado en el puerto
  8443; la verificación de cadena se desactiva en el scraper y se
  documenta abiertamente en el README. La integridad del dato se
  garantiza por verificación cruzada (tablero público, rangos
  operativos, respaldo en archivo web), no por TLS.
