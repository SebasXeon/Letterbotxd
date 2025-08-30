from __future__ import annotations

import os
from pathlib import Path
from typing import Union

import requests
from parsel import Selector

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; Letterbotxd/0.1; +https://github.com/SebasXeon/Letterbotxd)"
    ),
    "X-Requested-With": "XMLHttpRequest", 
}

def download_letterboxd_poster(
    endpoint_url: str,
    dest_path: Union[str, Path],
    *,
    hi_res: bool = True,
    timeout: int = 15,
) -> Path:
    # 1. Obtener el HTML del póster
    r = requests.get(endpoint_url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    sel = Selector(text=r.text)

    # 2. Extraer la URL de la imagen
    img = sel.xpath("//img[contains(@class,'image')]")
    if not img:
        raise RuntimeError("No se encontró la etiqueta <img> en el HTML del póster.")

    if hi_res and (srcset := img.attrib.get("srcset")):
        # toma el último elemento de srcset (normalmente la versión @2x)
        image_url = srcset.split()[-2]  # formato: URL 2x
    else:
        image_url = img.attrib["src"]

    # 3. Resolver destino
    dest_path = Path(dest_path).expanduser().resolve()
    if dest_path.is_dir() or dest_path.suffix == "":
        # Guardar con el mismo nombre del fichero remoto
        filename = Path(image_url).name.split("?")[0]  # quita params
        dest_path = dest_path / filename

    dest_path.parent.mkdir(parents=True, exist_ok=True)

    # 4. Descargar la imagen binaria
    with requests.get(image_url, headers=HEADERS, timeout=timeout, stream=True) as resp:
        resp.raise_for_status()
        with open(dest_path, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=8192):
                fh.write(chunk)

    return dest_path

def download_image(
    url: str,
    dest_path: Union[str, Path],
    timeout: int = 15,
) -> Path:
    # 1. Resolver destino
    dest_path = Path(dest_path).expanduser().resolve()
    if dest_path.is_dir() or dest_path.suffix == "":
        # Guardar con el mismo nombre del fichero remoto
        filename = Path(url).name.split("?")[0]  # quita params
        dest_path = dest_path / filename

    dest_path.parent.mkdir(parents=True, exist_ok=True)

    # 2. Descargar la imagen binaria
    with requests.get(url, headers=HEADERS, timeout=timeout, stream=True) as resp:
        resp.raise_for_status()
        with open(dest_path, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=8192):
                fh.write(chunk)

    return dest_path
