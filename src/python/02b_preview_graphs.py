#!/usr/bin/env python3
"""
Previsualización visual de los grafos generados en Fase 2 sobre el mapa real (2048x2048).
Genera dos imágenes PNG en results/figures/:
  - preview_01_macro_poi_graph.png   (16 POIs, aristas escasas y tamaño según nº de cofres)
  - preview_02_micro_chests_graph.png (todos los cofres individuales y aristas k-NN)

Uso (desde la carpeta raíz del proyecto):
  python src/python/02b_preview_graphs.py
"""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.image as mpimg

RAW_DIR = Path("data/raw")
PROC_DIR = Path("data/processed")
FIG_DIR = Path("results/figures")


def read_edges(graph_path: Path):
    edges = []
    with graph_path.open("r", encoding="utf-8") as f:
        header = f.readline().split()
        n, m = int(header[0]), int(header[1])
        for _ in range(n):
            f.readline()  # saltar nodos (usaremos sus píxeles de node_pixels.json)
        for _ in range(m):
            u, v, w_s, dist_m, factor = f.readline().split()
            edges.append((int(u), int(v), float(w_s), float(factor)))
    return edges


def load_map_background(ax):
    img_path = RAW_DIR / "map_crossbones_2026_blank.png"
    if img_path.exists():
        img = mpimg.imread(img_path)
        ax.imshow(img, extent=[0, 2048, 2048, 0], alpha=0.88)
    else:
        ax.set_facecolor("#0f172a")
        ax.set_xlim(400, 1750)
        ax.set_ylim(1750, 400)


def plot_macro(pixels: dict, edges: list, out_path: Path):
    pois = pixels["macro_pois"]
    fig, ax = plt.subplots(figsize=(11, 11), dpi=150)
    load_map_background(ax)

    # Dibujar aristas
    for u, v, w_s, factor in edges:
        x1, y1 = pois[u]["x_px"], pois[u]["y_px"]
        x2, y2 = pois[v]["x_px"], pois[v]["y_px"]
        is_bridge = factor > 1.01
        ax.plot(
            [x1, x2],
            [y1, y2],
            color="#f97316" if is_bridge else "#38bdf8",
            linestyle="--" if is_bridge else "-",
            linewidth=2.2 if is_bridge else 1.5,
            alpha=0.85,
            zorder=2,
        )

    # Dibujar nodos (tamaño proporcional al número de cofres)
    xs = [p["x_px"] for p in pois]
    ys = [p["y_px"] for p in pois]
    sizes = [80 + p["chests"] * 9 for p in pois]
    ax.scatter(xs, ys, s=sizes, c="#facc15", edgecolors="#111827", linewidths=1.5, zorder=3)

    for p in pois:
        ax.annotate(
            f"{p['name']}\n({p['chests']} cofres)",
            (p["x_px"], p["y_px"]),
            xytext=(0, -18),
            textcoords="offset points",
            ha="center",
            va="top",
            fontsize=8,
            fontweight="bold",
            color="white",
            bbox=dict(boxstyle="round,pad=0.2", fc="#0f172a", ec="none", alpha=0.72),
            zorder=4,
        )

    ax.set_xlim(450, 1720)
    ax.set_ylim(1740, 520)
    ax.set_title("Grafo Macro Real — Crossbones Isle (16 POIs, aristas escasas k=3)", fontsize=13, pad=12)
    ax.set_xlabel("X (píxeles del mapa 2048×2048)")
    ax.set_ylabel("Y (píxeles del mapa 2048×2048)")
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def plot_micro(pixels: dict, edges: list, out_path: Path):
    chests = pixels["micro_island"]
    fig, ax = plt.subplots(figsize=(11, 11), dpi=150)
    load_map_background(ax)

    # Dibujar aristas k-NN
    for u, v, _, factor in edges:
        x1, y1 = chests[u]["x_px"], chests[u]["y_px"]
        x2, y2 = chests[v]["x_px"], chests[v]["y_px"]
        is_bridge = factor > 1.01
        ax.plot(
            [x1, x2],
            [y1, y2],
            color="#ef4444" if is_bridge else "#e2e8f0",
            linewidth=1.2 if is_bridge else 0.45,
            alpha=0.85 if is_bridge else 0.45,
            zorder=2,
        )

    palette = {
        "chest": ("#facc15", "Cofre normal"),
        "buried_chest": ("#f97316", "Cofre enterrado"),
        "rare_chest": ("#38bdf8", "Cofre raro"),
    }
    for ctype, (color, label) in palette.items():
        subset = [c for c in chests if c["type"] == ctype]
        if subset:
            ax.scatter(
                [c["x_px"] for c in subset],
                [c["y_px"] for c in subset],
                s=18 if ctype == "chest" else 28,
                c=color,
                edgecolors="#111827",
                linewidths=0.4,
                label=f"{label} ({len(subset)})",
                zorder=3,
            )

    ax.set_xlim(450, 1720)
    ax.set_ylim(1740, 520)
    ax.legend(loc="upper right", facecolor="#0f172a", labelcolor="white", framealpha=0.85)
    ax.set_title(f"Grafo Micro Real — {len(chests)} cofres individuales (k=4 + puentes en rojo)", fontsize=13, pad=12)
    ax.set_xlabel("X (píxeles del mapa 2048×2048)")
    ax.set_ylabel("Y (píxeles del mapa 2048×2048)")
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def main() -> int:
    pixels_path = PROC_DIR / "node_pixels.json"
    macro_path = PROC_DIR / "macro_poi_sparse.graph"
    micro_path = PROC_DIR / "micro_island_sparse.graph"

    if not pixels_path.exists():
        print("[ERROR] Ejecuta primero: python src/python/02_build_graphs.py", file=sys.stderr)
        return 1

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    pixels = json.loads(pixels_path.read_text(encoding="utf-8"))

    out_macro = FIG_DIR / "preview_01_macro_poi_graph.png"
    out_micro = FIG_DIR / "preview_02_micro_chests_graph.png"

    plot_macro(pixels, read_edges(macro_path), out_macro)
    plot_micro(pixels, read_edges(micro_path), out_micro)

    print("[OK] Imágenes generadas:")
    print(f"  - {out_macro}")
    print(f"  - {out_micro}")
    return 0


if __name__ == "__main__":
    sys.exit(main())