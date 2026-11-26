#!/usr/bin/env python3
"""
Genera un mapa limpio con cada cofre individual representado como un punto amarillo pequeño,
sin aristas ni líneas de grafo.

Salida:
  - results/figures/preview_03_chests_dots_only.png

Uso (desde la carpeta raíz del proyecto):
  python src/python/02c_plot_chests_only.py
"""

import json
import sys
from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt

RAW_DIR = Path("data/raw")
PROC_DIR = Path("data/processed")
FIG_DIR = Path("results/figures")


def main() -> int:
    pixels_path = PROC_DIR / "node_pixels.json"
    if not pixels_path.exists():
        print("[ERROR] Ejecuta primero: python src/python/02_build_graphs.py", file=sys.stderr)
        return 1

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    pixels = json.loads(pixels_path.read_text(encoding="utf-8"))
    chests = pixels["micro_island"]

    fig, ax = plt.subplots(figsize=(12, 12), dpi=220)

    img_path = RAW_DIR / "map_crossbones_2026_blank.png"
    if img_path.exists():
        img = mpimg.imread(img_path)
        ax.imshow(img, extent=[0, 2048, 2048, 0], alpha=0.92)
    else:
        ax.set_facecolor("#0f172a")

    xs = [c["x_px"] for c in chests]
    ys = [c["y_px"] for c in chests]

    ax.scatter(
        xs,
        ys,
        s=10,                  # Tamaño del punto (bájalo a 6 si los quieres aún más pequeños)
        c="#facc15",           # Amarillo vivo
        edgecolors="#111827",  # Borde oscuro fino para distinguir cofres cercanos
        linewidths=0.35,
        alpha=0.95,
        zorder=3,
    )

    ax.set_xlim(450, 1720)
    ax.set_ylim(1740, 520)
    ax.set_title(
        f"Distribución real de cofres individuales — Crossbones Isle ({len(chests)} cofres)",
        fontsize=13,
        pad=12,
    )
    ax.set_xlabel("X (píxeles del mapa 2048×2048)")
    ax.set_ylabel("Y (píxeles del mapa 2048×2048)")

    out_path = FIG_DIR / "preview_03_chests_dots_only.png"
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)

    print(f"[OK] Imagen guardada en: {out_path} ({len(chests)} cofres individuales)")
    return 0


if __name__ == "__main__":
    sys.exit(main())