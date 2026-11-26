# Resumen Técnico Automático de Resultados (Fase 4 — T4)

Este documento resume los valores exactos generados por el núcleo C++17 para integrarlos en la Memoria PDF (Fase 5).

## 0. Verificación cruzada de algoritmos

- **E2 (Dijkstra Matriz == Dijkstra Lista == Floyd):** PASS (100%)
- **E3 (Coste Prim == Coste Kruskal):** PASS (100%)
- **E4 (Puntos de Articulación Ingenuo == Lineal nbpp/bajo):** PASS (100%)

## 1. Experimento E1 — TSP (Exacto vs. Heurísticas)

- Mayor instancia exacta resuelta: `macro_poi_complete` (n=16) en **172.964 ms** (2217107 estados, óptimo garantizado=True).
- Error medio de **MST + BPP** frente al óptimo: **10.94%** (máx. 31.82%, muy lejos de la cota teórica del 100%).
- Error medio de **Vecino Más Cercano** frente al óptimo: **8.24%** (máx. 13.84%).

## 2. Experimento E2 — Caminos Mínimos y Centralidad

- **Isla completa escasa (n=1034, m=2648):** Matriz = 8352.8 KB vs. Listas = 130.6 KB (**ahorro de memoria: 98.4%**).
  - Todos los pares: `n×Dijkstra Lista` = **88.22 ms** vs. `Floyd` = **150.27 ms** (ratio Floyd/n-Dijkstra = **1.70×**).
- **Isla completa densa (n=1034, m=534061):** `Floyd` = **1646.86 ms** vs. `n×Dijkstra Lista` = **2874.28 ms** vs. `n×Dijkstra Matriz` = **4256.62 ms**.
- **POI más céntrico (ponderado por cofres):** `Giants_Battlefield` (93.4 s de media). **Más periférico:** `Busy_Bay` (174.5 s).

## 3. Experimento E3 — MST (Prim vs. Kruskal) y Escuadrón de 4

- **Isla escasa (n=1034, m=2648):** Prim = 3.928 ms vs. Kruskal = **0.251 ms** (coste MST = 4169.9 s).
- **Isla completa (n=1034, m=534061):** Prim = **4.274 ms** vs. Kruskal = 67.015 ms (coste MST = 4037.6 s).
- **Reparto Macro 4 Escuadrones (Kruskal):** J1: 10 POIs (253 cofres), J2: 2 POIs (85 cofres), J3: 3 POIs (82 cofres), J4: 1 POIs (42 cofres).

## 4. Experimento E4 — Puntos de Articulación

- **Isla escasa (n=1034, m=2648):** Ingenuo = 28.540 ms vs. Lineal `nbpp`/`bajo` = **0.0509 ms** (**Speedup = 560.2×**). Detectados **85** puntos de articulación.

## 5. Experimento E5 — Estrategia Óptima del Token Pirata (T_lobby = 90 s)

| Estrategia | Jugadores | Cofres/hora | Horas P=50% (Normal) | Horas P=50% (2×) | Horas P=90% (2×) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `Squad4_Top4_POIs_Repeat` | 4 | **1758.9** | 54.2 h | 27.1 h | 90.0 h |
| `Squad4_Sin_Coordinacion_1POI` | 4 | **947.3** | 100.6 h | 50.3 h | 167.1 h |
| `Squad4_Particionado_MST_Isla` | 4 | **842.5** | 113.1 h | 56.6 h | 187.9 h |
| `Solo_Rotacion_Top3_POIs` | 1 | **499.1** | 191.0 h | 95.5 h | 317.2 h |
| `Solo_Loot_Lobby_Repeat_1POI` | 1 | **482.3** | 197.6 h | 98.8 h | 328.2 h |
| `Solo_Rotacion_Completa_TSP` | 1 | **467.8** | 203.7 h | 101.9 h | 338.4 h |
