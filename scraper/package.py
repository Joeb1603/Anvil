"""Build empire-wiki-archive.zip: the complete archive, with local-only pages overlaid."""
from __future__ import annotations

import os
import zipfile

from .common import DATA, LOCAL, ROOT, WIKI


def package(name: str = "empire-wiki-archive.zip") -> str:
    files: dict[str, str] = {}
    for base, prefix in ((WIKI, "wiki"), (DATA, "data"), (LOCAL / "wiki", "wiki"), (LOCAL / "data", "data")):
        for root, _dirs, names in os.walk(base):
            for n in names:
                full = os.path.join(root, n)
                files[os.path.join(prefix, os.path.relpath(full, base))] = full  # later bases override
    out = ROOT / name
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for arc in sorted(files):
            z.write(files[arc], arc)
    return f"{out} ({len(files)} files, {out.stat().st_size / 1e6:.1f} MB)"


if __name__ == "__main__":
    print(package())
