# Plantilla de web con Django de OEES

Esta plantilla sirve para crear una web pública que guarda datos: formularios, registros, contenido que cambia o usuarios que inician sesión. Tiene servidor (Django) y base de datos.

Si tu web solo tiene páginas, textos, imágenes y partes interactivas sin guardar datos, usa la plantilla estática (`oees-template-static`). Es más sencilla. Claude te dice cuál necesitas.

Si tu web es solo para empleados de OEES, no necesitas esta plantilla. Claude la prepara para Alexandria, la plataforma interna de OEES, y la publicas tú.

## Cómo trabajar

1. Abre Claude en modo Cowork. La skill `oees-web-infra` tiene que estar activada.
2. Explica qué web quieres. Claude te dice qué plantilla descargar.
3. Descarga esta plantilla: en GitHub, pulsa **Code** y después **Download ZIP**.
4. Crea una carpeta para tus webs, por ejemplo `Webs` en Documentos. Descomprime el zip dentro.
5. Da a Claude acceso a la carpeta `Webs`. Claude construye la web ahí y te cuenta cómo queda.
6. Para seguir otro día, abre Cowork con la misma carpeta.
7. Cuando la web esté lista, pide a Claude el zip para tecnología. Envíalo al equipo de tecnología. Tecnología la revisa, prepara la base de datos y la publica.
8. Después de publicarla, tecnología te devuelve un zip nuevo. Dáselo a Claude antes del siguiente cambio.

Si trabajas en un chat y no en Cowork, sube el zip al chat. Para seguir otro día, sube el último zip que te dio Claude.

## Tres reglas

- No pongas contraseñas, claves ni tokens en ningún archivo.
- No uses datos reales de clientes, ni siquiera para probar. Usa datos inventados.
- No hagas el zip a mano. Pide a Claude que lo genere: así no incluye archivos que no deben salir de tu equipo.

## Para el equipo de tecnología

- [`HANDOFF.md`](HANDOFF.md): qué contiene la web, qué datos guarda y qué hay que revisar.
- [`docs/deploy-runbook.md`](docs/deploy-runbook.md): cómo importar el zip, preparar la base de datos y publicar.
- [`docs/troubleshooting.md`](docs/troubleshooting.md): qué hacer si falla un despliegue.
- Las reglas del kit: `.claude/skills/django-drf/SKILL.md` y `.claude/skills/htmx-alpine/SKILL.md`.
