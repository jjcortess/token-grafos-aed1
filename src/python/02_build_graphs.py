#!/usr/bin/env python3
"""
Fase 2 (T3.1) - Construcción de grafos reales (.graph) a partir de MapSpawns.json (v43.10, 2026).

Entradas en data/raw/:
  - MapSpawns.json             (obligatorio: spawns reales de Crossbones Isle v43.10)
  - pois_crossbones_2026.csv   (opcional: generado por 01_fetch_snapshot.py para calibrar m/px)

Salidas en data/processed/:
  - macro_poi_sparse.graph / macro_poi_complete.graph       (16 POIs reales con sus cofres reales)
  - micro_tsp_n{6,8,10,11,12,20,45}_complete.graph          (subgrafos reales para E1: TSP)
  - micro_scale_n{50,100,200,400}_{sparse,complete}.graph   (escalabilidad real para E2, E3, E4)
  - micro_island_{sparse,complete}.graph                    (todos los cofres reales de la isla)
  - build_manifest.json                                     (resumen exacto + SHA-256 + conteos)
  - node_pixels.json                                        (coordenadas px para mapas en Fase 4)

Uso (desde la carpeta raíz del proyecto):
  python src/python/02_build_graphs.py
"""

import csv
import hashlib
import json
import math
import re
import sys
from collections import Counter, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

RAW_DIR = Path("data/raw")
OUT_DIR = Path("data/processed")

# Constantes físicas del modelo espacial
DEFAULT_METERS_PER_PX = 1.46484375  # 3000 m / 2048 px (se recalibra si existe pois_crossbones_2026.csv)
UE_UNITS_PER_METER = 100.0
BASE_SPEED_MPS = 6.0                # Velocidad media combinando carrera (5.5 m/s) y esprint (8.0 m/s)
CHEST_OPEN_SEC = 1.2                # Tiempo base de apertura de cofre
BURIED_CHEST_EXTRA_SEC = 2.0        # Tiempo extra de excavación en cofres enterrados
INTRA_POI_STEP_SEC = 4.5            # Desplazamiento medio entre cofres dentro del mismo POI (nivel macro)
SAME_PIXEL_FLOOR_SEC = 1.5          # Tiempo mínimo si dos cofres comparten (x, y) en distinta planta

# Tipos de spawn válidos para el Token Pirata en MapSpawns.json
CHEST_TYPES = {"chest", "buried_chest", "rare_chest"}


@dataclass
class Node:
    node_id: int
    x_m: float
    y_m: float
    x_px: float
    y_px: float
    chests: int
    loot_time_s: float
    label: str
    poi_group: str
    chest_type: str = "poi"


def sanitize_label(text: str) -> str:
    clean = re.sub(r"\s+", "_", text.strip())
    clean = re.sub(r"[^A-Za-z0-9_-]", "", clean)
    return clean or "Nodo"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def calibrate_meters_per_pixel(
    locations_px: Dict[str, List[float]], pois_csv: Path
) -> Tuple[float, str]:
    """Calcula la escala real metros/píxel emparejando los POIs de MapSpawns.json y Fortnite-API."""
    if not pois_csv.exists():
        return DEFAULT_METERS_PER_PX, "default_3000m_2048px"

    ue_coords: Dict[str, Tuple[float, float]] = {}
    with pois_csv.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ue_coords[row["poi_name"].strip()] = (
                float(row["x_ue"]) / UE_UNITS_PER_METER,
                float(row["y_ue"]) / UE_UNITS_PER_METER,
            )

    common = [name for name in locations_px if name in ue_coords]
    ratios = []
    for i in range(len(common)):
        for j in range(i + 1, len(common)):
            a, b = common[i], common[j]
            d_px = math.hypot(
                locations_px[a][0] - locations_px[b][0],
                locations_px[a][1] - locations_px[b][1],
            )
            d_m = math.hypot(
                ue_coords[a][0] - ue_coords[b][0],
                ue_coords[a][1] - ue_coords[b][1],
            )
            if d_px > 100.0 and d_m > 0.0:
                ratios.append(d_m / d_px)

    if not ratios:
        return DEFAULT_METERS_PER_PX, "default_3000m_2048px"

    ratios.sort()
    median_scale = ratios[len(ratios) // 2]
    return median_scale, f"calibrated_median_{len(common)}_pois"


def euclidean_m(a: Node, b: Node) -> float:
    return math.hypot(a.x_m - b.x_m, a.y_m - b.y_m)


def edge_weight_s(dist_m: float, factor: float = 1.0) -> float:
    if dist_m < 1e-6:
        return SAME_PIXEL_FLOOR_SEC
    return max(SAME_PIXEL_FLOOR_SEC, (dist_m / BASE_SPEED_MPS) * factor)


def build_complete_edges(nodes: List[Node]) -> List[Tuple[int, int, float, float, float]]:
    edges = []
    n = len(nodes)
    for i in range(n):
        for j in range(i + 1, n):
            dist = euclidean_m(nodes[i], nodes[j])
            edges.append((i, j, edge_weight_s(dist, 1.0), dist, 1.0))
    return edges


def ensure_connected(
    nodes: List[Node],
    edge_map: Dict[Tuple[int, int], Tuple[float, float, float]],
) -> int:
    """Conecta componentes desconectados añadiendo el enlace más corto entre islas. Devuelve puentes añadidos."""
    n = len(nodes)
    bridges_added = 0
    while True:
        adj: List[List[int]] = [[] for _ in range(n)]
        for u, v in edge_map:
            adj[u].append(v)
            adj[v].append(u)

        comp = [-1] * n
        cid = 0
        for start in range(n):
            if comp[start] != -1:
                continue
            q = deque([start])
            comp[start] = cid
            while q:
                u = q.popleft()
                for w in adj[u]:
                    if comp[w] == -1:
                        comp[w] = cid
                        q.append(w)
            cid += 1

        if cid <= 1:
            return bridges_added

        best_pair = None
        best_dist = float("inf")
        for i in range(n):
            if comp[i] != 0:
                continue
            for j in range(n):
                if comp[j] == 0:
                    continue
                d = euclidean_m(nodes[i], nodes[j])
                if d < best_dist:
                    best_dist = d
                    best_pair = (min(i, j), max(i, j))

        u, v = best_pair
        # Penalización 1.5x al tratarse de un enlace puente entre zonas separadas/agua
        edge_map[(u, v)] = (edge_weight_s(best_dist, 1.5), best_dist, 1.5)
        bridges_added += 1


def build_sparse_knn_edges(
    nodes: List[Node], k: int = 4
) -> Tuple[List[Tuple[int, int, float, float, float]], int]:
    n = len(nodes)
    edge_map: Dict[Tuple[int, int], Tuple[float, float, float]] = {}

    for i in range(n):
        dists = []
        for j in range(n):
            if i == j:
                continue
            dists.append((euclidean_m(nodes[i], nodes[j]), j))
        dists.sort()
        for dist, j in dists[: min(k, n - 1)]:
            u, v = (i, j) if i < j else (j, i)
            if (u, v) not in edge_map:
                edge_map[(u, v)] = (edge_weight_s(dist, 1.0), dist, 1.0)

    bridges = ensure_connected(nodes, edge_map)
    edges = [(u, v, vals[0], vals[1], vals[2]) for (u, v), vals in sorted(edge_map.items())]
    return edges, bridges


def reindex(nodes: List[Node]) -> List[Node]:
    return [
        Node(i, nd.x_m, nd.y_m, nd.x_px, nd.y_px, nd.chests, nd.loot_time_s, nd.label, nd.poi_group, nd.chest_type)
        for i, nd in enumerate(nodes)
    ]


def write_graph(
    path: Path,
    nodes: List[Node],
    edges: List[Tuple[int, int, float, float, float]],
    directed: int = 0,
    bridges: int = 0,
) -> dict:
    with path.open("w", encoding="utf-8") as f:
        f.write(f"{len(nodes)} {len(edges)} {directed}\n")
        for idx, nd in enumerate(nodes):
            f.write(
                f"{idx} {nd.x_m:.3f} {nd.y_m:.3f} {nd.chests} {nd.loot_time_s:.2f} {nd.label}\n"
            )
        for u, v, w_s, dist_m, factor in edges:
            f.write(f"{u} {v} {w_s:.3f} {dist_m:.3f} {factor:.2f}\n")

    n = len(nodes)
    density = (2.0 * len(edges)) / (n * (n - 1)) if n > 1 else 0.0
    return {
        "file": path.name,
        "nodes": n,
        "edges": len(edges),
        "directed": bool(directed),
        "density": round(density, 4),
        "bridges_added": bridges,
    }


def main() -> int:
    spawns_path = RAW_DIR / "MapSpawns.json"
    pois_csv = RAW_DIR / "pois_crossbones_2026.csv"

    if not spawns_path.exists():
        print(
            f"[ERROR] No se encuentra {spawns_path}.\n"
            "        Guarda tu archivo MapSpawns.json en data/raw/MapSpawns.json y vuelve a ejecutar.",
            file=sys.stderr,
        )
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    raw = json.loads(spawns_path.read_text(encoding="utf-8"))

    types: List[str] = raw["types"]
    places: List[str] = raw["places"]
    locations_px: Dict[str, List[float]] = raw["locations"]
    points: List[List[int]] = raw["points"]

    meters_per_px, scale_mode = calibrate_meters_per_pixel(locations_px, pois_csv)

    # 1. Extraer todos los cofres reales (chest, buried_chest, rare_chest)
    type_counts_all = Counter()
    poi_chest_counts: Dict[str, Counter] = {p: Counter() for p in places}
    chests: List[Node] = []

    for pt in points:
        t_idx, x_px, y_px, place_idx = pt
        t_name = types[t_idx]
        type_counts_all[t_name] += 1

        if t_name not in CHEST_TYPES:
            continue

        poi_name = places[place_idx] if 0 <= place_idx < len(places) else "Wild"
        if poi_name in poi_chest_counts:
            poi_chest_counts[poi_name][t_name] += 1

        loot_s = CHEST_OPEN_SEC + (BURIED_CHEST_EXTRA_SEC if t_name == "buried_chest" else 0.0)
        cid = len(chests)
        chests.append(
            Node(
                node_id=cid,
                x_m=round(x_px * meters_per_px, 3),
                y_m=round(y_px * meters_per_px, 3),
                x_px=float(x_px),
                y_px=float(y_px),
                chests=1,
                loot_time_s=round(loot_s, 2),
                label=f"{sanitize_label(poi_name)}_{t_name[0].upper()}{cid:03d}",
                poi_group=poi_name,
                chest_type=t_name,
            )
        )

    # 2. Construir nodos macro (los 16 lugares reales con su inventario exacto extraído de MapSpawns.json)
    macro_nodes: List[Node] = []
    poi_summary = []
    for idx, pname in enumerate(places):
        x_px, y_px = locations_px[pname]
        c_norm = poi_chest_counts[pname]["chest"]
        c_bur = poi_chest_counts[pname]["buried_chest"]
        c_rare = poi_chest_counts[pname]["rare_chest"]
        total_c = c_norm + c_bur + c_rare
        loot_time = (
            total_c * (CHEST_OPEN_SEC + INTRA_POI_STEP_SEC)
            + c_bur * BURIED_CHEST_EXTRA_SEC
        )
        macro_nodes.append(
            Node(
                node_id=idx,
                x_m=round(x_px * meters_per_px, 3),
                y_m=round(y_px * meters_per_px, 3),
                x_px=float(x_px),
                y_px=float(y_px),
                chests=total_c,
                loot_time_s=round(loot_time, 2),
                label=sanitize_label(pname),
                poi_group=pname,
                chest_type="poi",
            )
        )
        poi_summary.append({
            "id": idx,
            "name": pname,
            "chest": c_norm,
            "buried_chest": c_bur,
            "rare_chest": c_rare,
            "total_chests": total_c,
            "x_px": x_px,
            "y_px": y_px,
        })

    # Exportar también el inventario limpio en CSV para referencia directa en la memoria
    inv_out = OUT_DIR / "poi_inventory_extracted_2026.csv"
    with inv_out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["id", "name", "chest", "buried_chest", "rare_chest", "total_chests", "x_px", "y_px"]
        )
        writer.writeheader()
        writer.writerows(sorted(poi_summary, key=lambda r: r["total_chests"], reverse=True))

    manifest = {
        "source_file": str(spawns_path),
        "source_sha256": sha256_file(spawns_path),
        "game_version": raw.get("version"),
        "date": raw.get("date"),
        "source_url": raw.get("source"),
        "meters_per_pixel": round(meters_per_px, 6),
        "scale_calibration": scale_mode,
        "total_points_raw": len(points),
        "counts_by_type_raw": dict(type_counts_all),
        "total_valid_chests": len(chests),
        "graphs": [],
    }

    # 3. Grafos Macro (16 POIs)
    macro_sparse_edges, macro_bridges = build_sparse_knn_edges(macro_nodes, k=3)
    manifest["graphs"].append(
        write_graph(OUT_DIR / "macro_poi_sparse.graph", macro_nodes, macro_sparse_edges, bridges=macro_bridges)
    )
    manifest["graphs"].append(
        write_graph(OUT_DIR / "macro_poi_complete.graph", macro_nodes, build_complete_edges(macro_nodes))
    )

    # 4. Subgrafos Micro para E1 (TSP Exacto vs. Heurísticas)
    # Ordenamos los cofres por cercanía al centro del POI con más cofres (p. ej. Rubber Resort / Lantern Landing)
    by_poi: Dict[str, List[Node]] = {}
    for c in chests:
        if c.poi_group != "Wild":
            by_poi.setdefault(c.poi_group, []).append(c)
    densest_poi_name, densest_chests = max(by_poi.items(), key=lambda kv: len(kv[1]))
    cx, cy = locations_px[densest_poi_name]
    tsp_ordered = sorted(chests, key=lambda nd: math.hypot(nd.x_px - cx, nd.y_px - cy))
    manifest["tsp_anchor_poi"] = densest_poi_name
    manifest["tsp_anchor_poi_chests"] = len(densest_chests)

    for n_size in [6, 8, 10, 11, 12, 20, 45]:
        if len(tsp_ordered) >= n_size:
            sub = reindex(tsp_ordered[:n_size])
            manifest["graphs"].append(
                write_graph(OUT_DIR / f"micro_tsp_n{n_size}_complete.graph", sub, build_complete_edges(sub))
            )

    # 5. Subgrafos Micro de escalabilidad (E2, E3, E4): escasos (k=4) y completos
    scale_sizes = [s for s in [50, 100, 200, 400] if s < len(chests)]
    for n_size in scale_sizes:
        sub = reindex(chests[:n_size])
        sp_edges, sp_bridges = build_sparse_knn_edges(sub, k=4)
        manifest["graphs"].append(
            write_graph(OUT_DIR / f"micro_scale_n{n_size}_sparse.graph", sub, sp_edges, bridges=sp_bridges)
        )
        manifest["graphs"].append(
            write_graph(OUT_DIR / f"micro_scale_n{n_size}_complete.graph", sub, build_complete_edges(sub))
        )

    # Isla completa (todos los cofres reales)
    island_nodes = reindex(chests)
    isl_sp_edges, isl_bridges = build_sparse_knn_edges(island_nodes, k=4)
    manifest["graphs"].append(
        write_graph(OUT_DIR / "micro_island_sparse.graph", island_nodes, isl_sp_edges, bridges=isl_bridges)
    )
    manifest["graphs"].append(
        write_graph(OUT_DIR / "micro_island_complete.graph", island_nodes, build_complete_edges(island_nodes))
    )

    # Guardar coordenadas en píxeles (2048x2048) para superponer rutas sobre map_crossbones_2026_blank.png en Fase 4
    node_pixels = {
        "width": raw.get("width", 2048),
        "height": raw.get("height", 2048),
        "macro_pois": [
            {"id": nd.node_id, "label": nd.label, "name": nd.poi_group, "x_px": nd.x_px, "y_px": nd.y_px, "chests": nd.chests}
            for nd in macro_nodes
        ],
        "micro_island": [
            {"id": nd.node_id, "label": nd.label, "poi": nd.poi_group, "type": nd.chest_type, "x_px": nd.x_px, "y_px": nd.y_px}
            for nd in island_nodes
        ],
    }
    (OUT_DIR / "node_pixels.json").write_text(
        json.dumps(node_pixels, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (OUT_DIR / "build_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"[OK] Procesado MapSpawns.json (v{raw.get('version')} - {raw.get('date')})")
    print(f"     Escala espacial: {meters_per_px:.4f} m/px ({scale_mode})")
    print(f"     Cofres reales válidos (chest + buried + rare): {len(chests)}")
    print(f"     POI más denso (ancla E1 TSP): {densest_poi_name} ({len(densest_chests)} cofres)")
    print("\nTop POIs por cofres reales en MapSpawns.json:")
    for row in sorted(poi_summary, key=lambda r: r["total_chests"], reverse=True)[:8]:
        print(
            f"  - {row['name']:24s} | total={row['total_chests']:3d} "
            f"(normal={row['chest']:2d}, enterrado={row['buried_chest']:2d}, raro={row['rare_chest']:2d})"
        )
    print(f"\nGrafos generados en {OUT_DIR}/:")
    for g in manifest["graphs"]:
        print(
            f"  - {g['file']:36s} | N={g['nodes']:4d} | M={g['edges']:7d} | densidad={g['density']:.4f}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())