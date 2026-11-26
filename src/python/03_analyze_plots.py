#!/usr/bin/env python3
"""
Fase 4 (T3.3 y T4) - Análisis experimental, visualización profesional y mapas reales.

Lee los CSV exportados por el núcleo C++17 (results/csv/) y las coordenadas reales
(data/processed/node_pixels.json + data/raw/map_crossbones_2026_blank.png) para generar:
  - 8 figuras de alta resolución (220 DPI) en results/figures/
  - Informe técnico automático con todas las métricas exactas en results/analysis_summary.md

Uso (desde la carpeta raíz del proyecto):
  python src/python/03_analyze_plots.py
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RAW_DIR = Path("data/raw")
PROC_DIR = Path("data/processed")
CSV_DIR = Path("results/csv")
FIG_DIR = Path("results/figures")
SUMMARY_PATH = Path("results/analysis_summary.md")

# Estilo visual homogéneo y apto para impresión en PDF
plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "#fafafa",
    "axes.edgecolor": "#cbd5e1",
    "axes.grid": True,
    "grid.color": "#e2e8f0",
    "grid.linestyle": "--",
    "grid.alpha": 0.8,
    "font.size": 10,
    "axes.titlesize": 11.5,
    "axes.titleweight": "bold",
    "axes.labelsize": 10,
    "legend.framealpha": 0.92,
})

# Paleta accesible (alta diferenciación)
C_BLUE = "#2563eb"
C_ORANGE = "#ea580c"
C_GREEN = "#16a34a"
C_RED = "#dc2626"
C_PURPLE = "#7c3aed"
C_CYAN = "#0891b2"
SQUAD_COLORS = ["#facc15", "#38bdf8", "#4ade80", "#f472b6"]


def safe_pos(series: pd.Series, floor: float = 1e-4) -> np.ndarray:
    """Evita ceros exactos en ejes logarítmicos."""
    return np.maximum(series.to_numpy(dtype=float), floor)


def draw_map_bg(ax, alpha: float = 0.86) -> None:
    img_path = RAW_DIR / "map_crossbones_2026_blank.png"
    if img_path.exists():
        img = mpimg.imread(img_path)
        ax.imshow(img, extent=[0, 2048, 2048, 0], alpha=alpha)
    else:
        ax.set_facecolor("#0f172a")
    ax.set_xlim(470, 1690)
    ax.set_ylim(1720, 540)
    ax.grid(False)


def read_graph_edges(graph_path: Path):
    edges = []
    if not graph_path.exists():
        return edges
    with graph_path.open("r", encoding="utf-8") as f:
        n, m, _ = map(int, f.readline().split())
        for _ in range(n):
            f.readline()
        for _ in range(m):
            parts = f.readline().split()
            edges.append((int(parts[0]), int(parts[1]), float(parts[2]), float(parts[4])))
    return edges


# =============================================================================
# FIGURA 1: E1 — Benchmark TSP (Exacto O(n!) vs. MST+BPP vs. Vecino Más Cercano)
# =============================================================================
def plot_e1_tsp_benchmark(df_e1: pd.DataFrame) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.2), dpi=220)

    estilos = {
        "Exacto_Backtracking": (C_RED, "o", "-", "Exacto (Backtracking + poda)"),
        "Heuristica_MST_BPP": (C_BLUE, "s", "-", "Heurística MST + BPP (2-aprox.)"),
        "Heuristica_Vecino_Cercano": (C_GREEN, "^", "--", "Heurística Vecino Más Cercano"),
    }

    # Panel A: Tiempo de ejecución en escala logarítmica
    for alg, (color, marker, ls, label) in estilos.items():
        sub = df_e1[df_e1["algoritmo"] == alg].sort_values("n")
        if sub.empty:
            continue
        ax1.plot(
            sub["n"],
            safe_pos(sub["tiempo_ms"], 1e-4),
            color=color,
            marker=marker,
            linestyle=ls,
            linewidth=2.0,
            markersize=6,
            label=label,
        )

    ax1.set_yscale("log")
    ax1.set_title("A) Explosión combinatoria: tiempo de ejecución (escala log)")
    ax1.set_xlabel("Número de nodos del subgrafo (n)")
    ax1.set_ylabel("Tiempo mediano de ejecución (ms)")
    ax1.legend(loc="upper left")

    # Panel B: Error porcentual de las heurísticas respecto al óptimo exacto
    sub_err = df_e1[
        (df_e1["algoritmo"] != "Exacto_Backtracking") & (df_e1["error_pct"] >= 0)
    ].sort_values("n")

    if not sub_err.empty:
        ns = sorted(sub_err["n"].unique())
        x = np.arange(len(ns))
        width = 0.36

        mst_errs = [
            sub_err[(sub_err["n"] == nv) & (sub_err["algoritmo"] == "Heuristica_MST_BPP")]["error_pct"].mean()
            for nv in ns
        ]
        nn_errs = [
            sub_err[(sub_err["n"] == nv) & (sub_err["algoritmo"] == "Heuristica_Vecino_Cercano")]["error_pct"].mean()
            for nv in ns
        ]

        b1 = ax2.bar(x - width / 2, mst_errs, width, color=C_BLUE, label="MST + BPP")
        b2 = ax2.bar(x + width / 2, nn_errs, width, color=C_GREEN, label="Vecino Más Cercano")

        for bars in (b1, b2):
            for bar in bars:
                h = bar.get_height()
                if np.isfinite(h):
                    ax2.text(
                        bar.get_x() + bar.get_width() / 2,
                        h + 0.6,
                        f"{h:.1f}%",
                        ha="center",
                        va="bottom",
                        fontsize=8,
                    )

        ax2.axhline(100.0, color=C_RED, linestyle=":", linewidth=1.3, label="Cota teórica 2-aprox. (+100%)")
        ax2.set_xticks(x)
        ax2.set_xticklabels([f"n={nv}" for nv in ns])
        ax2.set_ylim(0, max(35.0, max(mst_errs + nn_errs, default=20.0) * 1.25))
        ax2.set_title("B) Calidad de ruta: desviación (%) frente al óptimo exacto")
        ax2.set_xlabel("Instancias verificadas con óptimo garantizado")
        ax2.set_ylabel("Error relativo sobre el óptimo (%)")
        ax2.legend(loc="upper right")

    fig.suptitle("Experimento E1: Problema del Viajante (TSP) — Precisión frente a Escalabilidad", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig01_e1_tsp_benchmark.png")
    plt.close(fig)


# =============================================================================
# FIGURA 2: E1 — Mapa real comparando Ruta TSP Exacta vs. Heurística MST+BPP
# =============================================================================
def plot_e1_map_tsp_macro(df_routes: pd.DataFrame, pixels: dict) -> None:
    pois = pixels["macro_pois"]
    sub = df_routes[df_routes["grafo"] == "macro_poi_complete"]
    if sub.empty:
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 7), dpi=200)
    paneles = [
        ("Exacto_Backtracking", C_RED, "Ruta TSP Óptima (Exacto)"),
        ("Heuristica_MST_BPP", C_BLUE, "Ruta Heurística MST + BPP"),
    ]

    for ax, (alg, color, titulo) in zip(axes, paneles):
        draw_map_bg(ax, alpha=0.88)
        fila = sub[sub["algoritmo"] == alg]
        if fila.empty:
            continue
        row = fila.iloc[0]
        ids = [int(x) for x in str(row["ruta_ids"]).split(";") if x != ""]

        # Dibujar ciclo cerrado
        for i in range(len(ids)):
            u = ids[i]
            v = ids[(i + 1) % len(ids)]
            x1, y1 = pois[u]["x_px"], pois[u]["y_px"]
            x2, y2 = pois[v]["x_px"], pois[v]["y_px"]
            ax.annotate(
                "",
                xy=(x2, y2),
                xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color=color, lw=2.3, alpha=0.92, shrinkA=7, shrinkB=7),
                zorder=3,
            )

        # Dibujar nodos y orden de visita
        for orden, nid in enumerate(ids, start=1):
            p = pois[nid]
            ax.scatter(p["x_px"], p["y_px"], s=95 + p["chests"] * 4, c="#facc15", edgecolors="#111827", lw=1.4, zorder=4)
            ax.text(p["x_px"], p["y_px"], str(orden), ha="center", va="center", fontsize=7.5, fontweight="bold", color="#111827", zorder=5)
            ax.annotate(
                p["name"],
                (p["x_px"], p["y_px"]),
                xytext=(0, -14),
                textcoords="offset points",
                ha="center",
                va="top",
                fontsize=7.2,
                color="white",
                bbox=dict(boxstyle="round,pad=0.18", fc="#0f172a", ec="none", alpha=0.72),
                zorder=4,
            )

        ax.set_title(f"{titulo}\nCiclo={row['coste_ciclo_s']:.1f} s | Ruta abierta={row['coste_abierto_s']:.1f} s")
        ax.set_xlabel("X (px)")
        ax.set_ylabel("Y (px)")

    fig.suptitle("Comparativa espacial sobre Crossbones Isle: Tour Macro de los 16 POIs", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig02_e1_map_tsp_macro.png")
    plt.close(fig)


# =============================================================================
# FIGURA 3: E2 — Caminos Mínimos (Memoria, Dijkstra 1-origen, Floyd vs n-Dijkstra)
# =============================================================================
def plot_e2_shortest_paths(df_e2: pd.DataFrame) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(13.5, 9.5), dpi=220)
    escaso = df_e2[df_e2["tipo"] == "escaso"].sort_values("n")
    completo = df_e2[df_e2["tipo"] == "completo"].sort_values("n")

    # A) Memoria: Matriz O(n²) vs Lista O(n+a) en grafo escaso
    ax = axes[0, 0]
    ax.plot(escaso["n"], escaso["mem_matriz_kb"], "o-", color=C_RED, lw=2, label="Matriz de adyacencia O(n²)")
    ax.plot(escaso["n"], escaso["mem_lista_kb"], "s-", color=C_BLUE, lw=2, label="Listas de adyacencia O(n+a) [escaso]")
    ax.plot(completo["n"], completo["mem_lista_kb"], "^--", color=C_PURPLE, lw=1.8, label="Listas de adyacencia [completo]")
    ax.set_title("A) Huella de memoria: Matriz vs. Listas de adyacencia")
    ax.set_xlabel("Número de nodos (n)")
    ax.set_ylabel("Memoria asignada (KB)")
    ax.legend()

    # B) Dijkstra 1 origen: Matriz O(n²) vs Lista O(a log n)
    ax = axes[0, 1]
    ax.plot(escaso["n"], safe_pos(escaso["dijkstra_matriz_1_ms"]), "o-", color=C_RED, lw=2, label="Dijkstra Matriz O(n²) [escaso]")
    ax.plot(escaso["n"], safe_pos(escaso["dijkstra_lista_1_ms"]), "s-", color=C_BLUE, lw=2, label="Dijkstra Lista O(a log n) [escaso]")
    ax.plot(completo["n"], safe_pos(completo["dijkstra_matriz_1_ms"]), "o--", color=C_ORANGE, lw=1.7, label="Dijkstra Matriz O(n²) [completo]")
    ax.plot(completo["n"], safe_pos(completo["dijkstra_lista_1_ms"]), "s--", color=C_CYAN, lw=1.7, label="Dijkstra Lista O(a log n) [completo]")
    ax.set_yscale("log")
    ax.set_title("B) Caminos mínimos desde un origen: Dijkstra Matriz vs. Lista")
    ax.set_xlabel("Número de nodos (n)")
    ax.set_ylabel("Tiempo mediano (ms, escala log)")
    ax.legend(fontsize=8.5)

    # C) Todos los pares en grafo ESCASO: Floyd O(n³) vs n*Dijkstra
    ax = axes[1, 0]
    ax.plot(escaso["n"], safe_pos(escaso["floyd_ms"]), "o-", color=C_RED, lw=2.2, label="Floyd O(n³)")
    ax.plot(escaso["n"], safe_pos(escaso["n_dijkstra_matriz_ms"]), "^--", color=C_ORANGE, lw=2.0, label="n × Dijkstra Matriz O(n³)")
    ax.plot(escaso["n"], safe_pos(escaso["n_dijkstra_lista_ms"]), "s-", color=C_BLUE, lw=2.2, label="n × Dijkstra Lista O(a·n log n)")
    ax.set_title("C) Todos los pares en grafo ESCASO (a << n²)")
    ax.set_xlabel("Número de nodos (n)")
    ax.set_ylabel("Tiempo mediano (ms)")
    ax.legend()

    # D) Todos los pares en grafo COMPLETO: Floyd O(n³) vs n*Dijkstra
    ax = axes[1, 1]
    ax.plot(completo["n"], safe_pos(completo["floyd_ms"]), "o-", color=C_RED, lw=2.2, label="Floyd O(n³)")
    ax.plot(completo["n"], safe_pos(completo["n_dijkstra_matriz_ms"]), "^--", color=C_ORANGE, lw=2.0, label="n × Dijkstra Matriz O(n³)")
    ax.plot(completo["n"], safe_pos(completo["n_dijkstra_lista_ms"]), "s-", color=C_BLUE, lw=2.2, label="n × Dijkstra Lista O(a·n log n)")
    ax.set_title("D) Todos los pares en grafo COMPLETO (a ≈ n²/2)")
    ax.set_xlabel("Número de nodos (n)")
    ax.set_ylabel("Tiempo mediano (ms)")
    ax.legend()

    fig.suptitle("Experimento E2: Representación y Caminos Mínimos (Dijkstra vs. Floyd)", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig03_e2_shortest_paths_scaling.png")
    plt.close(fig)


# =============================================================================
# FIGURA 4: E2 — Centralidad de POIs (Floyd) y Alcanzabilidad en k saltos (BPA)
# =============================================================================
def plot_e2_centrality_and_bpa(df_cent: pd.DataFrame, df_bpa: pd.DataFrame) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.8), dpi=220)

    # Panel A: Ranking de POIs más céntricos
    df_sorted = df_cent.sort_values("distancia_ponderada_cofres_s", ascending=True)
    y = np.arange(len(df_sorted))
    ax1.barh(y - 0.18, df_sorted["tiempo_medio_s"], height=0.35, color=C_BLUE, label="Tiempo medio al resto de POIs")
    ax1.barh(y + 0.18, df_sorted["distancia_ponderada_cofres_s"], height=0.35, color=C_ORANGE, label="Tiempo medio ponderado por cofres")
    ax1.set_yticks(y)
    ax1.set_yticklabels([f"{r.etiqueta} ({r.cofres}c)" for r in df_sorted.itertuples()], fontsize=8.5)
    ax1.invert_yaxis()
    ax1.set_title("A) Centralidad temporal de los 16 POIs (Floyd)")
    ax1.set_xlabel("Tiempo medio de desplazamiento (segundos)")
    ax1.legend(loc="lower right", fontsize=8.5)

    # Panel B: Alcanzabilidad BPA en k = 1..4 saltos para POIs representativos
    centro = df_sorted.iloc[0]["etiqueta"]
    periferia = df_sorted.iloc[-1]["etiqueta"]
    mas_cofres = df_cent.sort_values("cofres", ascending=False).iloc[0]["etiqueta"]
    destacados = list(dict.fromkeys([centro, mas_cofres, periferia]))

    # Media global de todos los POIs
    media_bpa = df_bpa.groupby("max_saltos")["cofres_alcanzados"].mean().reset_index()
    ax2.plot(media_bpa["max_saltos"], media_bpa["cofres_alcanzados"], "k:", lw=2.0, label="Media de la isla")

    colores_bpa = [C_BLUE, C_GREEN, C_RED]
    etiquetas_rol = {
        centro: f"{centro} (más céntrico)",
        mas_cofres: f"{mas_cofres} (más cofres)",
        periferia: f"{periferia} (más periférico)",
    }
    for etiq, col in zip(destacados, colores_bpa):
        sub = df_bpa[df_bpa["etiqueta"] == etiq].sort_values("max_saltos")
        ax2.plot(sub["max_saltos"], sub["cofres_alcanzados"], "o-", color=col, lw=2.2, markersize=6, label=etiquetas_rol.get(etiq, etiq))

    ax2.set_xticks([1, 2, 3, 4])
    ax2.set_title("B) Cofres alcanzables a ≤ k saltos mediante BPA")
    ax2.set_xlabel("Radio de búsqueda en saltos sobre la red escasa (k)")
    ax2.set_ylabel("Cofres acumulados alcanzables")
    ax2.legend(loc="lower right", fontsize=8.5)

    fig.suptitle("Análisis topológico de Crossbones Isle: Centro Temporal y Expansión BPA", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig04_e2_centrality_and_bpa.png")
    plt.close(fig)


# =============================================================================
# FIGURA 5: E3 — Benchmark Prim O(n²) vs. Kruskal O(a log a)
# =============================================================================
def plot_e3_mst_benchmark(df_e3: pd.DataFrame) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.0), dpi=220)

    escaso = df_e3[df_e3["tipo"] == "escaso"].sort_values("n")
    completo = df_e3[df_e3["tipo"] == "completo"].sort_values("n")

    ax1.plot(escaso["n"], safe_pos(escaso["prim_ms"]), "o-", color=C_RED, lw=2.2, label="Prim O(n²) [Matriz]")
    ax1.plot(escaso["n"], safe_pos(escaso["kruskal_ms"]), "s-", color=C_BLUE, lw=2.2, label="Kruskal O(a log a) [Union-Find]")
    ax1.set_title("A) Grafo ESCASO (a ≈ 4n): ventaja de Kruskal")
    ax1.set_xlabel("Número de nodos (n)")
    ax1.set_ylabel("Tiempo mediano (ms)")
    ax1.legend()

    ax2.plot(completo["n"], safe_pos(completo["prim_ms"]), "o-", color=C_RED, lw=2.2, label="Prim O(n²) [Matriz]")
    ax2.plot(completo["n"], safe_pos(completo["kruskal_ms"]), "s-", color=C_BLUE, lw=2.2, label="Kruskal O(a log a) [Union-Find]")
    ax2.set_title("B) Grafo COMPLETO (a ≈ n²/2): ventaja de Prim")
    ax2.set_xlabel("Número de nodos (n)")
    ax2.set_ylabel("Tiempo mediano (ms)")
    ax2.legend()

    fig.suptitle("Experimento E3: Árbol de Expansión Mínimo — Prim vs. Kruskal según densidad", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig05_e3_mst_benchmark.png")
    plt.close(fig)


# =============================================================================
# FIGURA 6: E3 — Mapas de Particionado en 4 Escuadrones mediante MST (Macro y Micro)
# =============================================================================
def plot_e3_map_squads(df_edges: pd.DataFrame, df_squad: pd.DataFrame, pixels: dict) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.5, 7.2), dpi=200)

    # Panel A: Macro (16 POIs) — MST completo (aristas cortadas en gris punteado) + 4 clústeres
    draw_map_bg(ax1, alpha=0.88)
    pois = pixels["macro_pois"]
    sq_macro = df_squad[df_squad["grafo"] == "macro_poi_complete"]
    ed_macro = df_edges[df_edges["grafo"] == "macro_poi_complete"]
    cluster_of_poi = dict(zip(sq_macro["nodo_id"], sq_macro["cluster_id"]))

    for row in ed_macro.itertuples():
        u, v = int(row.u), int(row.v)
        cu, cv = cluster_of_poi.get(u, -1), cluster_of_poi.get(v, -1)
        same = (cu == cv and cu >= 0)
        ax1.plot(
            [pois[u]["x_px"], pois[v]["x_px"]],
            [pois[u]["y_px"], pois[v]["y_px"]],
            color=SQUAD_COLORS[cu % 4] if same else "#ef4444",
            linestyle="-" if same else ":",
            linewidth=2.6 if same else 1.8,
            alpha=0.95 if same else 0.75,
            zorder=2,
        )

    for cid in sorted(sq_macro["cluster_id"].unique()):
        sub = sq_macro[sq_macro["cluster_id"] == cid]
        total_c = int(sub["cluster_total_cofres"].iloc[0])
        xs = [pois[int(nid)]["x_px"] for nid in sub["nodo_id"]]
        ys = [pois[int(nid)]["y_px"] for nid in sub["nodo_id"]]
        sizes = [90 + pois[int(nid)]["chests"] * 6 for nid in sub["nodo_id"]]
        ax1.scatter(
            xs, ys, s=sizes, c=SQUAD_COLORS[int(cid) % 4], edgecolors="#111827", lw=1.4,
            label=f"Jugador {int(cid)+1}: {len(sub)} POIs ({total_c} cofres)", zorder=4,
        )

    for p in pois:
        ax1.annotate(
            p["name"], (p["x_px"], p["y_px"]), xytext=(0, -13), textcoords="offset points",
            ha="center", va="top", fontsize=7.0, color="white",
            bbox=dict(boxstyle="round,pad=0.16", fc="#0f172a", ec="none", alpha=0.72), zorder=5,
        )
    ax1.set_title("A) Macro MST (16 POIs): 4 zonas de escuadrón\n(en rojo punteado: las 3 aristas más caras cortadas)")
    ax1.legend(loc="lower left", facecolor="#0f172a", labelcolor="white", fontsize=8)

    # Panel B: Micro (todos los cofres reales de la isla) — 4 clústeres de escuadrón
    draw_map_bg(ax2, alpha=0.88)
    chests = pixels["micro_island"]
    sq_micro = df_squad[df_squad["grafo"] == "micro_island_complete"]
    ed_micro = df_edges[df_edges["grafo"] == "micro_island_complete"]
    cluster_of_chest = dict(zip(sq_micro["nodo_id"], sq_micro["cluster_id"]))

    for row in ed_micro.itertuples():
        u, v = int(row.u), int(row.v)
        cu, cv = cluster_of_chest.get(u, -1), cluster_of_chest.get(v, -1)
        if cu == cv and cu >= 0:
            ax2.plot(
                [chests[u]["x_px"], chests[v]["x_px"]],
                [chests[u]["y_px"], chests[v]["y_px"]],
                color=SQUAD_COLORS[cu % 4], lw=0.9, alpha=0.65, zorder=2,
            )

    for cid in sorted(sq_micro["cluster_id"].unique()):
        sub = sq_micro[sq_micro["cluster_id"] == cid]
        total_c = int(sub["cluster_total_cofres"].iloc[0])
        xs = [chests[int(nid)]["x_px"] for nid in sub["nodo_id"]]
        ys = [chests[int(nid)]["y_px"] for nid in sub["nodo_id"]]
        ax2.scatter(
            xs, ys, s=16, c=SQUAD_COLORS[int(cid) % 4], edgecolors="#111827", lw=0.35,
            label=f"Zona {int(cid)+1}: {total_c} cofres", zorder=3,
        )

    ax2.set_title(f"B) Micro MST ({len(chests)} cofres reales): particionado automático en 4 sectores")
    ax2.legend(loc="lower left", facecolor="#0f172a", labelcolor="white", fontsize=8.5)

    fig.suptitle("Particionado Multiagente para Escuadrón de 4 Jugadores (Clustering por Kruskal)", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig06_e3_map_squad_clusters.png")
    plt.close(fig)


# =============================================================================
# FIGURA 7: E4 — Puntos de Articulación (Ingenuo vs. Lineal nbpp/bajo + Mapa)
# =============================================================================
def plot_e4_articulation(df_e4: pd.DataFrame, df_nodes: pd.DataFrame, pixels: dict) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6.2), dpi=220)
    df_s = df_e4.sort_values("n")

    # Panel A: Tiempo de ejecución + anotación de Speedup
    ax1.plot(df_s["n"], safe_pos(df_s["ingenuo_ms"]), "o-", color=C_RED, lw=2.2, label="Ingenuo O(n(n+a))")
    ax1.plot(df_s["n"], safe_pos(df_s["lineal_ms"]), "s-", color=C_BLUE, lw=2.2, label="Lineal nbpp/bajo O(n+a)")
    ax1.set_yscale("log")

    for r in df_s.itertuples():
        if r.speedup > 1.0:
            ax1.annotate(
                f"{r.speedup:.0f}×",
                (r.n, max(r.ingenuo_ms, 1e-4)),
                xytext=(0, 8),
                textcoords="offset points",
                ha="center",
                fontsize=8.5,
                fontweight="bold",
                color=C_RED,
            )

    ax1.set_title("A) Rendimiento: Eliminación iterativa vs. algoritmo lineal nbpp/bajo")
    ax1.set_xlabel("Número de nodos del grafo escaso (n)")
    ax1.set_ylabel("Tiempo mediano (ms, escala log)")
    ax1.legend(loc="upper left")

    # Panel B: Mapa real de micro_island_sparse destacando los puntos de articulación
    draw_map_bg(ax2, alpha=0.86)
    chests = pixels["micro_island"]
    edges = read_graph_edges(PROC_DIR / "micro_island_sparse.graph")

    for u, v, _, factor in edges:
        is_bridge = factor > 1.01
        ax2.plot(
            [chests[u]["x_px"], chests[v]["x_px"]],
            [chests[u]["y_px"], chests[v]["y_px"]],
            color="#fb923c" if is_bridge else "#cbd5e1",
            lw=1.3 if is_bridge else 0.45,
            alpha=0.85 if is_bridge else 0.4,
            zorder=2,
        )

    art_micro = df_nodes[df_nodes["grafo"] == "micro_island_sparse"]
    art_ids = set(art_micro["nodo_id"].astype(int).tolist())

    norm_x = [c["x_px"] for c in chests if c["id"] not in art_ids]
    norm_y = [c["y_px"] for c in chests if c["id"] not in art_ids]
    ax2.scatter(norm_x, norm_y, s=11, c="#facc15", edgecolors="#111827", lw=0.25, alpha=0.8, label="Cofre estándar", zorder=3)

    if art_ids:
        art_x = [chests[i]["x_px"] for i in art_ids]
        art_y = [chests[i]["y_px"] for i in art_ids]
        ax2.scatter(
            art_x, art_y, s=55, c=C_RED, edgecolors="white", lw=0.9, marker="D",
            label=f"Punto de articulación ({len(art_ids)} nodos críticos)", zorder=5,
        )

    ax2.set_title("B) Cuellos de botella geográficos sobre la red escasa de cofres")
    ax2.legend(loc="lower left", facecolor="#0f172a", labelcolor="white", fontsize=8.5)

    fig.suptitle("Experimento E4: Detección de Puntos de Articulación (Resiliencia de Rotaciones)", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig07_e4_articulation_benchmark_and_map.png")
    plt.close(fig)


# =============================================================================
# FIGURA 8: E5 — Simulación Aplicada del Token Pirata (Cofres/h y Horas P50/P90)
# =============================================================================
def plot_e5_token_simulation(df_e5: pd.DataFrame) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.5, 5.8), dpi=220)

    nombres_cortos = {
        "Solo_Loot_Lobby_Repeat_1POI": "Solo: 1 POI\n+ Lobby Repeat",
        "Solo_Rotacion_Top3_POIs": "Solo: Rotación\nTop-3 POIs",
        "Solo_Rotacion_Completa_TSP": "Solo: Isla\nCompleta (TSP)",
        "Squad4_Sin_Coordinacion_1POI": "Squad 4: Sin\ncoord. (1 POI)",
        "Squad4_Top4_POIs_Repeat": "Squad 4: Top-4\nPOIs disjuntos",
        "Squad4_Particionado_MST_Isla": "Squad 4: MST\nIsla Completa",
    }
    orden = list(nombres_cortos.keys())

    # Panel A: Cofres/hora según tiempo de espera en vestíbulo (modo Normal)
    df_norm = df_e5[df_e5["modo_evento"] == "Normal_1_en_137500"]
    x = np.arange(len(orden))
    width = 0.26
    lobbies = [60.0, 90.0, 120.0]
    colores_l = [C_GREEN, C_BLUE, C_ORANGE]

    for idx, (tl, col) in enumerate(zip(lobbies, colores_l)):
        sub = df_norm[df_norm["t_lobby_s"] == tl].set_index("estrategia")
        vals = [sub.loc[e, "cofres_por_hora"] if e in sub.index else 0.0 for e in orden]
        bars = ax1.bar(x + (idx - 1) * width, vals, width, color=col, label=f"T_lobby = {int(tl)} s")
        if tl == 90.0:
            for b, v in zip(bars, vals):
                ax1.text(b.get_x() + b.get_width() / 2, v + 12, f"{v:.0f}", ha="center", va="bottom", fontsize=7.8, fontweight="bold")

    ax1.set_xticks(x)
    ax1.set_xticklabels([nombres_cortos[e] for e in orden], fontsize=8.3)
    ax1.set_title("A) Productividad efectiva (cofres/hora) según T_lobby")
    ax1.set_ylabel("Cofres abiertos por hora")
    ax1.legend(loc="upper left")

    # Panel B: Horas necesarias para P = 50% de obtener el Token (T_lobby = 90s)
    df_90 = df_e5[df_e5["t_lobby_s"] == 90.0]
    norm_90 = df_90[df_90["modo_evento"] == "Normal_1_en_137500"].set_index("estrategia")
    th2x_90 = df_90[df_90["modo_evento"] == "TreasureHours2x_1_en_68750"].set_index("estrategia")

    vals_norm_p50 = [norm_90.loc[e, "horas_p50"] if e in norm_90.index else 0.0 for e in orden]
    vals_2x_p50 = [th2x_90.loc[e, "horas_p50"] if e in th2x_90.index else 0.0 for e in orden]

    w2 = 0.36
    b1 = ax2.bar(x - w2 / 2, vals_norm_p50, w2, color=C_PURPLE, label="Probabilidad normal (1 / 137.500)")
    b2 = ax2.bar(x + w2 / 2, vals_2x_p50, w2, color=C_CYAN, label="Treasure Hours 2× (1 / 68.750)")

    for bars in (b1, b2):
        for bar in bars:
            h = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width() / 2, h + 3, f"{h:.0f}h", ha="center", va="bottom", fontsize=7.8)

    ax2.set_xticks(x)
    ax2.set_xticklabels([nombres_cortos[e] for e in orden], fontsize=8.3)
    ax2.set_title("B) Horas de juego para alcanzar P = 50% de éxito (T_lobby = 90 s)")
    ax2.set_ylabel("Horas acumuladas hasta P = 50%")
    ax2.legend(loc="upper right")

    fig.suptitle("Experimento E5: Optimización Real del Evento «Token Pirata» (Noviembre 2026)", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig08_e5_token_pirata_strategy.png")
    plt.close(fig)


# =============================================================================
# INFORME AUTOMÁTICO EN MARKDOWN (para verificar resultados y redactar Fase 5)
# =============================================================================
def write_markdown_summary(
    df_e1: pd.DataFrame,
    df_e2: pd.DataFrame,
    df_cent: pd.DataFrame,
    df_e3: pd.DataFrame,
    df_squad: pd.DataFrame,
    df_e4: pd.DataFrame,
    df_e5: pd.DataFrame,
) -> None:
    lines: List[str] = [
        "# Resumen Técnico Automático de Resultados (Fase 4 — T4)\n",
        "Este documento resume los valores exactos generados por el núcleo C++17 para integrarlos en la Memoria PDF (Fase 5).\n",
    ]

    # Verificaciones cruzadas
    ok_e2 = int(df_e2["verificacion_ok"].min()) == 1
    ok_e3 = int(df_e3["verificacion_ok"].min()) == 1
    ok_e4 = int(df_e4["verificacion_ok"].min()) == 1
    lines.append("## 0. Verificación cruzada de algoritmos\n")
    lines.append(f"- **E2 (Dijkstra Matriz == Dijkstra Lista == Floyd):** {'PASS (100%)' if ok_e2 else 'REVISAR'}")
    lines.append(f"- **E3 (Coste Prim == Coste Kruskal):** {'PASS (100%)' if ok_e3 else 'REVISAR'}")
    lines.append(f"- **E4 (Puntos de Articulación Ingenuo == Lineal nbpp/bajo):** {'PASS (100%)' if ok_e4 else 'REVISAR'}\n")

    # E1
    lines.append("## 1. Experimento E1 — TSP (Exacto vs. Heurísticas)\n")
    ex = df_e1[df_e1["algoritmo"] == "Exacto_Backtracking"].sort_values("n")
    mst_h = df_e1[(df_e1["algoritmo"] == "Heuristica_MST_BPP") & (df_e1["error_pct"] >= 0)]
    nn_h = df_e1[(df_e1["algoritmo"] == "Heuristica_Vecino_Cercano") & (df_e1["error_pct"] >= 0)]
    if not ex.empty:
        max_ex = ex.iloc[-1]
        lines.append(f"- Mayor instancia exacta resuelta: `{max_ex['grafo']}` (n={int(max_ex['n'])}) en **{max_ex['tiempo_ms']:.3f} ms** ({int(max_ex['estados_explorados'])} estados, óptimo garantizado={bool(max_ex['optimo_garantizado'])}).")
    if not mst_h.empty:
        lines.append(f"- Error medio de **MST + BPP** frente al óptimo: **{mst_h['error_pct'].mean():.2f}%** (máx. {mst_h['error_pct'].max():.2f}%, muy lejos de la cota teórica del 100%).")
    if not nn_h.empty:
        lines.append(f"- Error medio de **Vecino Más Cercano** frente al óptimo: **{nn_h['error_pct'].mean():.2f}%** (máx. {nn_h['error_pct'].max():.2f}%).\n")

    # E2
    lines.append("## 2. Experimento E2 — Caminos Mínimos y Centralidad\n")
    isl_sp = df_e2[df_e2["grafo"] == "micro_island_sparse"]
    isl_cp = df_e2[df_e2["grafo"] == "micro_island_complete"]
    if not isl_sp.empty:
        r = isl_sp.iloc[0]
        ahorro_mem = (1.0 - r["mem_lista_kb"] / r["mem_matriz_kb"]) * 100.0
        lines.append(f"- **Isla completa escasa (n={int(r['n'])}, m={int(r['m'])}):** Matriz = {r['mem_matriz_kb']:.1f} KB vs. Listas = {r['mem_lista_kb']:.1f} KB (**ahorro de memoria: {ahorro_mem:.1f}%**).")
        lines.append(f"  - Todos los pares: `n×Dijkstra Lista` = **{r['n_dijkstra_lista_ms']:.2f} ms** vs. `Floyd` = **{r['floyd_ms']:.2f} ms** (ratio Floyd/n-Dijkstra = **{r['floyd_ms']/max(r['n_dijkstra_lista_ms'],1e-6):.2f}×**).")
    if not isl_cp.empty:
        r = isl_cp.iloc[0]
        lines.append(f"- **Isla completa densa (n={int(r['n'])}, m={int(r['m'])}):** `Floyd` = **{r['floyd_ms']:.2f} ms** vs. `n×Dijkstra Lista` = **{r['n_dijkstra_lista_ms']:.2f} ms** vs. `n×Dijkstra Matriz` = **{r['n_dijkstra_matriz_ms']:.2f} ms**.")
    if not df_cent.empty:
        c_top = df_cent.sort_values("distancia_ponderada_cofres_s").iloc[0]
        c_bot = df_cent.sort_values("distancia_ponderada_cofres_s").iloc[-1]
        lines.append(f"- **POI más céntrico (ponderado por cofres):** `{c_top['etiqueta']}` ({c_top['distancia_ponderada_cofres_s']:.1f} s de media). **Más periférico:** `{c_bot['etiqueta']}` ({c_bot['distancia_ponderada_cofres_s']:.1f} s).\n")

    # E3
    lines.append("## 3. Experimento E3 — MST (Prim vs. Kruskal) y Escuadrón de 4\n")
    e3_sp = df_e3[df_e3["grafo"] == "micro_island_sparse"]
    e3_cp = df_e3[df_e3["grafo"] == "micro_island_complete"]
    if not e3_sp.empty:
        r = e3_sp.iloc[0]
        lines.append(f"- **Isla escasa (n={int(r['n'])}, m={int(r['m'])}):** Prim = {r['prim_ms']:.3f} ms vs. Kruskal = **{r['kruskal_ms']:.3f} ms** (coste MST = {r['coste_kruskal_s']:.1f} s).")
    if not e3_cp.empty:
        r = e3_cp.iloc[0]
        lines.append(f"- **Isla completa (n={int(r['n'])}, m={int(r['m'])}):** Prim = **{r['prim_ms']:.3f} ms** vs. Kruskal = {r['kruskal_ms']:.3f} ms (coste MST = {r['coste_kruskal_s']:.1f} s).")
    sq_m = df_squad[df_squad["grafo"] == "macro_poi_complete"].groupby("cluster_id").agg(
        pois=("nodo_id", "count"), cofres=("cluster_total_cofres", "first")
    )
    if not sq_m.empty:
        reparto = ", ".join(f"J{i+1}: {int(row.pois)} POIs ({int(row.cofres)} cofres)" for i, row in sq_m.iterrows())
        lines.append(f"- **Reparto Macro 4 Escuadrones (Kruskal):** {reparto}.\n")

    # E4
    lines.append("## 4. Experimento E4 — Puntos de Articulación\n")
    e4_isl = df_e4[df_e4["grafo"] == "micro_island_sparse"]
    if not e4_isl.empty:
        r = e4_isl.iloc[0]
        lines.append(f"- **Isla escasa (n={int(r['n'])}, m={int(r['m'])}):** Ingenuo = {r['ingenuo_ms']:.3f} ms vs. Lineal `nbpp`/`bajo` = **{r['lineal_ms']:.4f} ms** (**Speedup = {r['speedup']:.1f}×**). Detectados **{int(r['num_puntos_art'])}** puntos de articulación.\n")

    # E5
    lines.append("## 5. Experimento E5 — Estrategia Óptima del Token Pirata (T_lobby = 90 s)\n")
    sub90_norm = df_e5[(df_e5["t_lobby_s"] == 90.0) & (df_e5["modo_evento"] == "Normal_1_en_137500")].sort_values("cofres_por_hora", ascending=False)
    sub90_2x = df_e5[(df_e5["t_lobby_s"] == 90.0) & (df_e5["modo_evento"] == "TreasureHours2x_1_en_68750")].set_index("estrategia")
    lines.append("| Estrategia | Jugadores | Cofres/hora | Horas P=50% (Normal) | Horas P=50% (2×) | Horas P=90% (2×) |")
    lines.append("| :--- | :---: | :---: | :---: | :---: | :---: |")
    for r in sub90_norm.itertuples():
        h50_2x = sub90_2x.loc[r.estrategia, "horas_p50"] if r.estrategia in sub90_2x.index else 0.0
        h90_2x = sub90_2x.loc[r.estrategia, "horas_p90"] if r.estrategia in sub90_2x.index else 0.0
        lines.append(f"| `{r.estrategia}` | {int(r.jugadores)} | **{r.cofres_por_hora:.1f}** | {r.horas_p50:.1f} h | {h50_2x:.1f} h | {h90_2x:.1f} h |")

    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    required = [
        "e1_tsp_benchmark.csv",
        "e1_tsp_routes.csv",
        "e2_shortest_paths_benchmark.csv",
        "e2_poi_centrality.csv",
        "e2_bpa_reachability.csv",
        "e3_mst_benchmark.csv",
        "e3_mst_edges.csv",
        "e3_squad_clusters.csv",
        "e4_articulation_benchmark.csv",
        "e4_articulation_nodes.csv",
        "e5_token_simulation.csv",
    ]
    missing = [f for f in required if not (CSV_DIR / f).exists()]
    if missing:
        print("[ERROR] Faltan CSVs generados por C++ en results/csv/:", file=sys.stderr)
        for m in missing:
            print(f"  - {m}", file=sys.stderr)
        print("Ejecuta primero el binario C++ (make run o .\\aed1_runner.exe all data/processed results/csv).", file=sys.stderr)
        return 1

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    pixels = json.loads((PROC_DIR / "node_pixels.json").read_text(encoding="utf-8"))

    df_e1 = pd.read_csv(CSV_DIR / "e1_tsp_benchmark.csv")
    df_e1_r = pd.read_csv(CSV_DIR / "e1_tsp_routes.csv")
    df_e2 = pd.read_csv(CSV_DIR / "e2_shortest_paths_benchmark.csv")
    df_cent = pd.read_csv(CSV_DIR / "e2_poi_centrality.csv")
    df_bpa = pd.read_csv(CSV_DIR / "e2_bpa_reachability.csv")
    df_e3 = pd.read_csv(CSV_DIR / "e3_mst_benchmark.csv")
    df_e3_e = pd.read_csv(CSV_DIR / "e3_mst_edges.csv")
    df_squad = pd.read_csv(CSV_DIR / "e3_squad_clusters.csv")
    df_e4 = pd.read_csv(CSV_DIR / "e4_articulation_benchmark.csv")
    df_e4_n = pd.read_csv(CSV_DIR / "e4_articulation_nodes.csv")
    df_e5 = pd.read_csv(CSV_DIR / "e5_token_simulation.csv")

    print("[1/8] Generando fig01_e1_tsp_benchmark.png ...")
    plot_e1_tsp_benchmark(df_e1)
    print("[2/8] Generando fig02_e1_map_tsp_macro.png ...")
    plot_e1_map_tsp_macro(df_e1_r, pixels)
    print("[3/8] Generando fig03_e2_shortest_paths_scaling.png ...")
    plot_e2_shortest_paths(df_e2)
    print("[4/8] Generando fig04_e2_centrality_and_bpa.png ...")
    plot_e2_centrality_and_bpa(df_cent, df_bpa)
    print("[5/8] Generando fig05_e3_mst_benchmark.png ...")
    plot_e3_mst_benchmark(df_e3)
    print("[6/8] Generando fig06_e3_map_squad_clusters.png ...")
    plot_e3_map_squads(df_e3_e, df_squad, pixels)
    print("[7/8] Generando fig07_e4_articulation_benchmark_and_map.png ...")
    plot_e4_articulation(df_e4, df_e4_n, pixels)
    print("[8/8] Generando fig08_e5_token_pirata_strategy.png ...")
    plot_e5_token_simulation(df_e5)

    write_markdown_summary(df_e1, df_e2, df_cent, df_e3, df_squad, df_e4, df_e5)

    print(f"\n[OK] 8 figuras guardadas en {FIG_DIR}/")
    print(f"[OK] Resumen tecnico generado en {SUMMARY_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())