# Procedencia de esta skill

| | |
| --- | --- |
| **Origen** | Oficial de FastAPI |
| **Repositorio** | https://github.com/fastapi/fastapi |
| **Ruta en upstream** | `fastapi/.agents/skills/fastapi/` |
| **Commit** | `0af003a85da454dcf6b6783e0ad3f0dd687e944f` (2026-06-25) |
| **Instalada** | 2026-09-21, con `npx skills add`, en el commit `763a4d7` de este repositorio |

Los siete ficheros son idénticos a los de ese commit. Se comprobó el 2026-09-24 descargando cada fichero de ese commit y comparándolo con el vendorizado, sin contar finales de línea.

**El hash `187b2e06` que figuraba antes en el README no es un commit**: GitHub no encuentra ningún commit con ese prefijo. Casi seguro era el `computedHash` de contenido que calcula `npx skills`, igual que el de `feature-sliced-design`; no se ha podido comprobar porque el `skills-lock.json` que lo guardaba no llegó a registrar esta skill.
