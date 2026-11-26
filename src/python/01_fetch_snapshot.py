#!/usr/bin/env python3
"""
Fase 2 (T3.1) - Descarga y congelación reproducible del mapa oficial de Fortnite.
Uso:
    python3 src/python/01_fetch_snapshot.py
    python3 src/python/01_fetch_snapshot.py --force
"""

import argparse
import csv
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API_URL = "https://fortnite-api.com/v1/map?language=es"
USER_AGENT = "AED1-UMU-GraphResearch/1.0 (Academic Project)"

RAW_DIR = Path("data/raw")
JSON_PATH = RAW_DIR / "map_crossbones_2026.json"
IMG_BLANK_PATH = RAW_DIR / "map_crossbones_2026_blank.png"
IMG_POIS_PATH = RAW_DIR / "map_crossbones_2026_pois.png"
POIS_CSV_PATH = RAW_DIR / "pois_crossbones_2026.csv"
INVENTORY_TEMPLATE_PATH = RAW_DIR / "poi_inventory_2026.csv"
META_PATH = RAW_DIR / "snapshot_metadata.json"
SHA_PATH = RAW_DIR / "SHA256SUMS.txt"


def download_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status} al descargar {url}")
        return resp.read()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Descarga y congela el snapshot oficial del mapa de Fortnite."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Sobrescribe un snapshot ya existente (NO usar tras el 5 de diciembre).",
    )
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if JSON_PATH.exists() and not args.force:
        print(f"[OK] Ya existe un snapshot congelado en {JSON_PATH}.")
        print("     Usa --force solo si realmente deseas volver a descargarlo.")
        return 0

    print(f"[1/4] Descargando JSON oficial desde {API_URL} ...")
    raw_json = download_bytes(API_URL)
    payload = json.loads(raw_json.decode("utf-8"))

    if payload.get("status") != 200 or "data" not in payload:
        raise RuntimeError(f"Respuesta inesperada de la API: {payload.get('status')}")

    JSON_PATH.write_bytes(raw_json)
    data = payload["data"]

    # Descargar imágenes del mapa (en blanco y con etiquetas) para la Fase 4
    images = data.get("images", {})
    if "blank" in images:
        print(f"[2/4] Descargando mapa limpio ({images['blank']}) ...")
        IMG_BLANK_PATH.write_bytes(download_bytes(images["blank"]))
    if "pois" in images:
        print(f"      Descargando mapa con POIs ({images['pois']}) ...")
        IMG_POIS_PATH.write_bytes(download_bytes(images["pois"]))

    # Extraer POIs con coordenadas exactas en unidades de Unreal Engine
    pois = data.get("pois", [])
    print(f"[3/4] Extrayendo {len(pois)} POIs oficiales a {POIS_CSV_PATH} ...")
    with POIS_CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["poi_id", "poi_name", "x_ue", "y_ue", "z_ue"])
        for p in sorted(pois, key=lambda item: item.get("name", "")):
            loc = p.get("location", {})
            writer.writerow([
                p.get("id", ""),
                p.get("name", "").strip(),
                loc.get("x", 0.0),
                loc.get("y", 0.0),
                loc.get("z", 0.0),
            ])

    # Crear plantilla de inventario si el grupo aún no la ha rellenado
    if not INVENTORY_TEMPLATE_PATH.exists():
        print(f"      Creando plantilla de inventario en {INVENTORY_TEMPLATE_PATH} ...")
        with INVENTORY_TEMPLATE_PATH.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["poi_name", "normal_chests", "buried_chests", "rare_chests"])
            for p in sorted(pois, key=lambda item: item.get("name", "")):
                writer.writerow([p.get("name", "").strip(), 0, 0, 0])
        print("      [AVISO] Rellena los recuentos reales de cofres en data/raw/poi_inventory_2026.csv.")

    # Guardar metadatos y hashes SHA-256 para auditabilidad
    print(f"[4/4] Generando firmas de integridad en {SHA_PATH} ...")
    tracked = [JSON_PATH, IMG_BLANK_PATH, IMG_POIS_PATH, POIS_CSV_PATH]
    checksums = {}
    with SHA_PATH.open("w", encoding="utf-8") as f:
        for path in tracked:
            if path.exists():
                digest = sha256_file(path)
                checksums[path.name] = digest
                f.write(f"{digest}  {path.name}\n")

    metadata = {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_url": API_URL,
        "num_pois": len(pois),
        "checksums_sha256": checksums,
    }
    META_PATH.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\nSnapshot congelado correctamente:")
    for p in sorted(pois, key=lambda item: item.get("name", "")):
        loc = p.get("location", {})
        print(f"  - {p.get('name', ''):22s} | x={loc.get('x', 0):9.1f}, y={loc.get('y', 0):9.1f}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)