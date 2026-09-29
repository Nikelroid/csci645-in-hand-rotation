"""Asset loading helper vendored from mjlab 1.1.1 (``mjlab.utils.os.update_assets``), which later mjlab releases removed."""

from pathlib import Path
from typing import Any, Dict


def update_assets(
  assets: Dict[str, Any],
  path: str | Path,
  meshdir: str | None = None,
  glob: str = "*",
  recursive: bool = False,
) -> None:
  """Add the files in ``path`` to ``assets``, keyed as ``<meshdir>/<name>`` when ``meshdir`` is given."""
  for f in Path(path).glob(glob):
    if f.is_file():
      asset_key = f"{meshdir}/{f.name}" if meshdir else f.name
      assets[asset_key] = f.read_bytes()
    elif f.is_dir() and recursive:
      update_assets(assets, f, meshdir, glob, recursive)
