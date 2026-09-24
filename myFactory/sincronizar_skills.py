"""Copia las skills de myFactory/skills/ a .claude/skills/, que es donde Claude Code las carga.

La fuente es myFactory/skills/; .claude/skills/ es una copia y no se edita a mano.
No se usan enlaces porque el repositorio tiene core.symlinks=false: git guardaría
un fichero de texto con la ruta y un clon en Windows no tendría skills.

    python myFactory/sincronizar_skills.py              # copia
    python myFactory/sincronizar_skills.py --comprobar  # falla si las dos difieren
"""

import filecmp
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FUENTE = RAIZ / "myFactory" / "skills"
DESTINO = RAIZ / ".claude" / "skills"


def diferencias() -> list[str]:
    fuera = []

    def recorrer(cmp: filecmp.dircmp, prefijo: str) -> None:
        fuera.extend(f"solo en myFactory: {prefijo}{n}" for n in cmp.left_only)
        fuera.extend(f"solo en .claude: {prefijo}{n}" for n in cmp.right_only)
        fuera.extend(f"distinto: {prefijo}{n}" for n in cmp.diff_files)
        for nombre, sub in cmp.subdirs.items():
            recorrer(sub, f"{prefijo}{nombre}/")

    if not DESTINO.exists():
        return ["no existe .claude/skills/"]
    recorrer(filecmp.dircmp(FUENTE, DESTINO, ignore=[]), "")
    return fuera


def main() -> int:
    if "--comprobar" in sys.argv:
        fuera = diferencias()
        for linea in fuera:
            print(linea)
        print("skills sincronizadas" if not fuera else f"{len(fuera)} diferencias: ejecuta sin --comprobar")
        return 1 if fuera else 0
    if DESTINO.exists():
        shutil.rmtree(DESTINO)
    shutil.copytree(FUENTE, DESTINO)
    print(f"copiadas {sum(1 for p in FUENTE.iterdir() if p.is_dir())} skills a .claude/skills/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
