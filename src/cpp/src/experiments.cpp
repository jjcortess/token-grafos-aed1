#include "experiments.hpp"
#include "articulation.hpp"
#include "graph.hpp"
#include "mst.hpp"
#include "shortest_paths.hpp"
#include "traversals.hpp"
#include "tsp.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <sstream>
#include <vector>

namespace fs = std::filesystem;

namespace aed1 {

namespace {

// Mide el tiempo mediano (en milisegundos) repitiendo la operación para eliminar ruido del SO
template <typename Func>
double medir_mediana_ms(Func&& fn, int min_reps = 5, double tiempo_objetivo_ms = 25.0, int max_reps = 300) {
    std::vector<double> tiempos;
    tiempos.reserve(static_cast<size_t>(min_reps));
    double acumulado = 0.0;

    for (int i = 0; i < max_reps; ++i) {
        auto t0 = std::chrono::steady_clock::now();
        fn();
        auto t1 = std::chrono::steady_clock::now();
        double ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
        tiempos.push_back(ms);
        acumulado += ms;
        if (i + 1 >= min_reps && acumulado >= tiempo_objetivo_ms) {
            break;
        }
    }

    std::sort(tiempos.begin(), tiempos.end());
    size_t mid = tiempos.size() / 2;
    if (tiempos.size() % 2 == 0) {
        return 0.5 * (tiempos[mid - 1] + tiempos[mid]);
    }
    return tiempos[mid];
}

std::string unir_ruta(const std::vector<int>& ruta) {
    std::ostringstream oss;
    for (size_t i = 0; i < ruta.size(); ++i) {
        if (i > 0) {
            oss << ";";
        }
        oss << ruta[i];
    }
    return oss.str();
}

// Construye un subgrafo completo de distancias mínimas para evaluar TSP sobre un subconjunto de nodos
GrafoCargado construir_subgrafo_completo(const GrafoMatriz& matriz_global,
                                         const std::vector<int>& indices_nodos,
                                         const std::string& nombre) {
    int k = static_cast<int>(indices_nodos.size());
    std::vector<Nodo> sub_nodos;
    sub_nodos.reserve(static_cast<size_t>(k));
    const auto& originales = matriz_global.nodos();

    for (int i = 0; i < k; ++i) {
        Nodo nd = originales[indices_nodos[i]];
        nd.id = i;
        sub_nodos.push_back(nd);
    }

    GrafoCargado sub;
    sub.nombre = nombre;
    sub.lista = GrafoLista(k, false, sub_nodos);
    sub.matriz = GrafoMatriz(k, false, sub_nodos);

    for (int i = 0; i < k; ++i) {
        for (int j = i + 1; j < k; ++j) {
            double c = matriz_global.coste(indices_nodos[i], indices_nodos[j]);
            sub.lista.insertar_arista({i, j, c, 0.0, 1.0});
            sub.matriz.insertar_arista(i, j, c);
        }
    }
    return sub;
}

}  // namespace

// ============================================================================
// E1: Problema del Viajante (TSP) — Exacto vs. MST+BPP vs. Vecino Más Cercano
// ============================================================================
void ejecutar_experimento_e1_tsp(const std::string& dir_grafos, const std::string& dir_csv) {
    std::cout << "\n[E1] Ejecutando benchmark TSP (Exacto vs. MST+BPP vs. Vecino Mas Cercano)...\n";

    std::vector<std::string> ficheros = {
        "micro_tsp_n6_complete.graph",
        "micro_tsp_n8_complete.graph",
        "micro_tsp_n10_complete.graph",
        "micro_tsp_n11_complete.graph",
        "micro_tsp_n12_complete.graph",
        "macro_poi_complete.graph",
        "micro_tsp_n20_complete.graph",
        "micro_tsp_n45_complete.graph"
    };

    std::ofstream f_bench(fs::path(dir_csv) / "e1_tsp_benchmark.csv");
    std::ofstream f_routes(fs::path(dir_csv) / "e1_tsp_routes.csv");

    f_bench << "grafo,n,m,algoritmo,tiempo_ms,coste_ciclo_s,coste_abierto_s,"
               "ratio_vs_exacto,error_pct,optimo_garantizado,estados_explorados\n";
    f_routes << "grafo,n,algoritmo,coste_ciclo_s,coste_abierto_s,ruta_ids\n";

    f_bench << std::fixed << std::setprecision(4);
    f_routes << std::fixed << std::setprecision(4);

    for (const auto& nombre_fich : ficheros) {
        fs::path ruta = fs::path(dir_grafos) / nombre_fich;
        if (!fs::exists(ruta)) {
            continue;
        }
        GrafoCargado g = cargar_grafo(ruta.string());
        int n = g.lista.num_nodos();
        int m = g.lista.num_aristas();

        // 1. Heurística Vecino Más Cercano
        ResultadoTSP res_nn;
        double t_nn = medir_mediana_ms([&]() {
            res_nn = tsp_vecino_mas_cercano(g.matriz, true);
        }, 7, 15.0);

        // 2. Heurística MST + BPP
        ResultadoTSP res_mst;
        double t_mst = medir_mediana_ms([&]() {
            res_mst = tsp_heuristica_mst_bpp(g.lista, g.matriz);
        }, 7, 15.0);

        // 3. Exacto por backtracking (hasta n <= 16; para n > 16 es computacionalmente intratable)
        bool ejecutar_exacto = (n <= 16);
        ResultadoTSP res_ex;
        double t_ex = -1.0;
        if (ejecutar_exacto) {
            int reps_ex = (n <= 10) ? 5 : 1;
            t_ex = medir_mediana_ms([&]() {
                res_ex = tsp_exacto_backtracking(g.matriz, 12.0);
            }, reps_ex, 10.0, (n <= 10) ? 50 : 3);
        }

        auto escribir_fila = [&](const std::string& alg, double t_ms, const ResultadoTSP& r) {
            double ratio = (ejecutar_exacto && res_ex.optimo_garantizado && res_ex.coste_ciclo > 0.0)
                               ? (r.coste_ciclo / res_ex.coste_ciclo)
                               : -1.0;
            double err_pct = (ratio > 0.0) ? ((ratio - 1.0) * 100.0) : -1.0;

            f_bench << g.nombre << "," << n << "," << m << "," << alg << ","
                    << t_ms << "," << r.coste_ciclo << "," << r.coste_abierto << ","
                    << ratio << "," << err_pct << "," << (r.optimo_garantizado ? 1 : 0) << ","
                    << r.estados_explorados << "\n";

            f_routes << g.nombre << "," << n << "," << alg << ","
                     << r.coste_ciclo << "," << r.coste_abierto << ","
                     << unir_ruta(r.ruta) << "\n";
        };

        if (ejecutar_exacto) {
            escribir_fila("Exacto_Backtracking", t_ex, res_ex);
        }
        escribir_fila("Heuristica_MST_BPP", t_mst, res_mst);
        escribir_fila("Heuristica_Vecino_Cercano", t_nn, res_nn);

        std::cout << "  - " << std::setw(26) << std::left << g.nombre
                  << " | N=" << std::setw(2) << std::right << n
                  << " | MST+BPP=" << std::fixed << std::setprecision(1) << res_mst.coste_ciclo << "s"
                  << " | NN=" << res_nn.coste_ciclo << "s";
        if (ejecutar_exacto) {
            std::cout << " | Exacto=" << res_ex.coste_ciclo << "s ("
                      << std::setprecision(3) << t_ex << " ms, estados=" << res_ex.estados_explorados << ")";
        } else {
            std::cout << " | Exacto=INTRATABLE (O(n!))";
        }
        std::cout << "\n";
    }
}

// ============================================================================
// E2: Caminos Mínimos (Dijkstra Matriz vs. Listas, Floyd vs. n-Dijkstra) + BPA
// ============================================================================
void ejecutar_experimento_e2_caminos(const std::string& dir_grafos, const std::string& dir_csv) {
    std::cout << "\n[E2] Ejecutando benchmark Caminos Minimos (Dijkstra, Floyd, Centralidad y BPA)...\n";

    std::vector<std::pair<std::string, std::string>> grafos = {
        {"macro_poi_sparse.graph", "escaso"},
        {"macro_poi_complete.graph", "completo"},
        {"micro_scale_n50_sparse.graph", "escaso"},
        {"micro_scale_n50_complete.graph", "completo"},
        {"micro_scale_n100_sparse.graph", "escaso"},
        {"micro_scale_n100_complete.graph", "completo"},
        {"micro_scale_n200_sparse.graph", "escaso"},
        {"micro_scale_n200_complete.graph", "completo"},
        {"micro_scale_n400_sparse.graph", "escaso"},
        {"micro_scale_n400_complete.graph", "completo"},
        {"micro_island_sparse.graph", "escaso"},
        {"micro_island_complete.graph", "completo"}
    };

    std::ofstream f_bench(fs::path(dir_csv) / "e2_shortest_paths_benchmark.csv");
    f_bench << "grafo,tipo,n,m,densidad,mem_matriz_kb,mem_lista_kb,"
               "dijkstra_matriz_1_ms,dijkstra_lista_1_ms,"
               "n_dijkstra_matriz_ms,n_dijkstra_lista_ms,floyd_ms,verificacion_ok\n";
    f_bench << std::fixed << std::setprecision(4);

    for (const auto& [fich, tipo] : grafos) {
        fs::path ruta = fs::path(dir_grafos) / fich;
        if (!fs::exists(ruta)) {
            continue;
        }
        GrafoCargado g = cargar_grafo(ruta.string());
        int n = g.lista.num_nodos();
        int m = g.lista.num_aristas();
        double dens = (n > 1) ? (2.0 * m) / (static_cast<double>(n) * (n - 1)) : 0.0;

        // 1. Dijkstra desde un único origen (nodo 0)
        ResultadoDijkstra d_mat, d_lst;
        double t_dm1 = medir_mediana_ms([&]() { d_mat = dijkstra_matriz(g.matriz, 0); }, 5, 10.0);
        double t_dl1 = medir_mediana_ms([&]() { d_lst = dijkstra_lista(g.lista, 0); }, 5, 10.0);

        // 2. Todos los pares: n * Dijkstra Matriz vs. n * Dijkstra Lista vs. Floyd
        int reps_apsp = (n <= 100) ? 5 : 3;
        double t_ndm = medir_mediana_ms([&]() {
            for (int s = 0; s < n; ++s) {
                volatile double sink = dijkstra_matriz(g.matriz, s).D[n - 1];
                (void)sink;
            }
        }, reps_apsp, 20.0, 20);

        double t_ndl = medir_mediana_ms([&]() {
            for (int s = 0; s < n; ++s) {
                volatile double sink = dijkstra_lista(g.lista, s).D[n - 1];
                (void)sink;
            }
        }, reps_apsp, 20.0, 20);

        ResultadoFloyd res_floyd;
        double t_floyd = medir_mediana_ms([&]() { res_floyd = floyd(g.matriz); }, reps_apsp, 20.0, 20);

        // Verificación cruzada exacta: Dijkstra matriz == Dijkstra lista == Floyd desde nodo 0
        bool ok = true;
        for (int v = 0; v < n; ++v) {
            if (std::fabs(d_mat.D[v] - d_lst.D[v]) > 1e-4 ||
                std::fabs(d_mat.D[v] - res_floyd.dist(0, v)) > 1e-4) {
                ok = false;
                break;
            }
        }

        double mem_mat_kb = static_cast<double>(g.matriz.memoria_bytes()) / 1024.0;
        double mem_lst_kb = static_cast<double>(g.lista.memoria_bytes()) / 1024.0;

        f_bench << g.nombre << "," << tipo << "," << n << "," << m << "," << dens << ","
                << mem_mat_kb << "," << mem_lst_kb << ","
                << t_dm1 << "," << t_dl1 << ","
                << t_ndm << "," << t_ndl << "," << t_floyd << ","
                << (ok ? 1 : 0) << "\n";

        std::cout << "  - " << std::setw(28) << std::left << g.nombre
                  << " | N=" << std::setw(3) << std::right << n
                  << " | n*DijkLista=" << std::setw(7) << std::setprecision(2) << t_ndl << "ms"
                  << " | Floyd=" << std::setw(7) << t_floyd << "ms"
                  << " | Check=" << (ok ? "PASS" : "FAIL") << "\n";
    }

    // Análisis de centralidad y alcanzabilidad BPA sobre el grafo real de 16 POIs
    fs::path ruta_macro = fs::path(dir_grafos) / "macro_poi_sparse.graph";
    if (fs::exists(ruta_macro)) {
        GrafoCargado macro = cargar_grafo(ruta_macro.string());
        ResultadoFloyd f = floyd(macro.matriz);
        int n = macro.lista.num_nodos();

        std::ofstream f_cent(fs::path(dir_csv) / "e2_poi_centrality.csv");
        f_cent << "id,etiqueta,cofres,tiempo_medio_s,excentricidad_max_s,distancia_ponderada_cofres_s\n";
        f_cent << std::fixed << std::setprecision(3);

        for (int i = 0; i < n; ++i) {
            double suma = 0.0;
            double max_d = 0.0;
            double suma_pond = 0.0;
            int total_cofres_otros = 0;

            for (int j = 0; j < n; ++j) {
                if (i == j) {
                    continue;
                }
                double d = f.dist(i, j);
                suma += d;
                max_d = std::max(max_d, d);
                suma_pond += d * macro.lista.nodos()[j].cofres;
                total_cofres_otros += macro.lista.nodos()[j].cofres;
            }
            double media = (n > 1) ? suma / (n - 1) : 0.0;
            double pond = (total_cofres_otros > 0) ? suma_pond / total_cofres_otros : 0.0;
            const auto& nd = macro.lista.nodos()[i];
            f_cent << nd.id << "," << nd.etiqueta << "," << nd.cofres << ","
                   << media << "," << max_d << "," << pond << "\n";
        }

        // Alcanzabilidad en k = 1, 2, 3 saltos mediante BPA (Tema 4.3.1.2)
        std::ofstream f_bpa(fs::path(dir_csv) / "e2_bpa_reachability.csv");
        f_bpa << "id,etiqueta,max_saltos,pois_alcanzados,cofres_alcanzados\n";
        for (int i = 0; i < n; ++i) {
            for (int k : {1, 2, 3, 4}) {
                ResultadoBPA bpa = busqueda_primero_anchura(macro.lista, i, k);
                f_bpa << i << "," << macro.lista.nodos()[i].etiqueta << ","
                      << k << "," << bpa.nodos_alcanzados << "," << bpa.cofres_alcanzados << "\n";
            }
        }
    }
}

// ============================================================================
// E3: Árboles de Expansión Mínimos (Prim vs. Kruskal) y 4 Escuadrones
// ============================================================================
void ejecutar_experimento_e3_mst_escuadron(const std::string& dir_grafos, const std::string& dir_csv) {
    std::cout << "\n[E3] Ejecutando benchmark MST (Prim vs. Kruskal) y particionado en 4 escuadrones...\n";

    std::vector<std::pair<std::string, std::string>> grafos = {
        {"macro_poi_sparse.graph", "escaso"},
        {"macro_poi_complete.graph", "completo"},
        {"micro_scale_n50_sparse.graph", "escaso"},
        {"micro_scale_n50_complete.graph", "completo"},
        {"micro_scale_n100_sparse.graph", "escaso"},
        {"micro_scale_n100_complete.graph", "completo"},
        {"micro_scale_n200_sparse.graph", "escaso"},
        {"micro_scale_n200_complete.graph", "completo"},
        {"micro_scale_n400_sparse.graph", "escaso"},
        {"micro_scale_n400_complete.graph", "completo"},
        {"micro_island_sparse.graph", "escaso"},
        {"micro_island_complete.graph", "completo"}
    };

    std::ofstream f_bench(fs::path(dir_csv) / "e3_mst_benchmark.csv");
    std::ofstream f_edges(fs::path(dir_csv) / "e3_mst_edges.csv");
    std::ofstream f_squad(fs::path(dir_csv) / "e3_squad_clusters.csv");

    f_bench << "grafo,tipo,n,m,prim_ms,kruskal_ms,coste_prim_s,coste_kruskal_s,verificacion_ok\n";
    f_edges << "grafo,u,v,peso_s\n";
    f_squad << "grafo,cluster_id,nodo_id,etiqueta,cofres,tiempo_saqueo_s,cluster_total_cofres,cluster_coste_mst_s\n";

    f_bench << std::fixed << std::setprecision(4);
    f_edges << std::fixed << std::setprecision(4);
    f_squad << std::fixed << std::setprecision(3);

    for (const auto& [fich, tipo] : grafos) {
        fs::path ruta = fs::path(dir_grafos) / fich;
        if (!fs::exists(ruta)) {
            continue;
        }
        GrafoCargado g = cargar_grafo(ruta.string());
        int n = g.lista.num_nodos();
        int m = g.lista.num_aristas();

        ResultadoMST r_prim, r_kruskal;
        double t_prim = medir_mediana_ms([&]() { r_prim = mst_prim(g.matriz); }, 5, 15.0);
        double t_kruskal = medir_mediana_ms([&]() { r_kruskal = mst_kruskal(g.lista); }, 5, 15.0);

        bool ok = r_prim.conexo && r_kruskal.conexo &&
                  (std::fabs(r_prim.coste_total - r_kruskal.coste_total) < 1e-3);

        f_bench << g.nombre << "," << tipo << "," << n << "," << m << ","
                << t_prim << "," << t_kruskal << ","
                << r_prim.coste_total << "," << r_kruskal.coste_total << ","
                << (ok ? 1 : 0) << "\n";

        std::cout << "  - " << std::setw(28) << std::left << g.nombre
                  << " | Prim=" << std::setw(7) << std::right << std::setprecision(3) << t_prim << "ms"
                  << " | Kruskal=" << std::setw(7) << t_kruskal << "ms"
                  << " | Coste=" << std::setprecision(1) << r_kruskal.coste_total << "s"
                  << " | Check=" << (ok ? "PASS" : "FAIL") << "\n";

        // Exportar aristas MST y clústeres de 4 jugadores para los mapas principales
        if (fich == "macro_poi_complete.graph" || fich == "micro_island_complete.graph") {
            for (const auto& a : r_kruskal.aristas) {
                f_edges << g.nombre << "," << a.u << "," << a.v << "," << a.peso << "\n";
            }
            auto clusters = particionar_escuadron_mst(g.lista, r_kruskal, 4);
            for (const auto& cl : clusters) {
                for (int nid : cl.nodos) {
                    const auto& nd = g.lista.nodos()[nid];
                    f_squad << g.nombre << "," << cl.cluster_id << "," << nid << ","
                            << nd.etiqueta << "," << nd.cofres << "," << nd.tiempo_saqueo << ","
                            << cl.total_cofres << "," << cl.coste_mst_interno << "\n";
                }
            }
        }
    }
}

// ============================================================================
// E4: Puntos de Articulación — Ingenuo O(n(n+a)) vs. Lineal nbpp/bajo O(n+a)
// ============================================================================
void ejecutar_experimento_e4_articulacion(const std::string& dir_grafos, const std::string& dir_csv) {
    std::cout << "\n[E4] Ejecutando benchmark Puntos de Articulacion (Ingenuo vs. nbpp/bajo)...\n";

    std::vector<std::string> grafos = {
        "macro_poi_sparse.graph",
        "micro_scale_n50_sparse.graph",
        "micro_scale_n100_sparse.graph",
        "micro_scale_n200_sparse.graph",
        "micro_scale_n400_sparse.graph",
        "micro_island_sparse.graph"
    };

    std::ofstream f_bench(fs::path(dir_csv) / "e4_articulation_benchmark.csv");
    std::ofstream f_nodes(fs::path(dir_csv) / "e4_articulation_nodes.csv");

    f_bench << "grafo,n,m,ingenuo_ms,lineal_ms,speedup,num_puntos_art,verificacion_ok\n";
    f_nodes << "grafo,nodo_id,etiqueta,cofres,grado\n";
    f_bench << std::fixed << std::setprecision(4);

    for (const auto& fich : grafos) {
        fs::path ruta = fs::path(dir_grafos) / fich;
        if (!fs::exists(ruta)) {
            continue;
        }
        GrafoCargado g = cargar_grafo(ruta.string());
        int n = g.lista.num_nodos();
        int m = g.lista.num_aristas();

        std::vector<int> art_ing, art_lin;
        double t_ing = medir_mediana_ms([&]() { art_ing = puntos_articulacion_ingenuo(g.lista); }, 5, 15.0);
        double t_lin = medir_mediana_ms([&]() { art_lin = puntos_articulacion_lineal(g.lista); }, 9, 15.0);

        bool ok = (art_ing == art_lin);
        double speedup = (t_lin > 1e-9) ? (t_ing / t_lin) : 0.0;

        f_bench << g.nombre << "," << n << "," << m << ","
                << t_ing << "," << t_lin << "," << speedup << ","
                << art_lin.size() << "," << (ok ? 1 : 0) << "\n";

        for (int v : art_lin) {
            const auto& nd = g.lista.nodos()[v];
            f_nodes << g.nombre << "," << v << "," << nd.etiqueta << ","
                    << nd.cofres << "," << g.lista.adyacentes(v).size() << "\n";
        }

        std::cout << "  - " << std::setw(28) << std::left << g.nombre
                  << " | N=" << std::setw(3) << std::right << n
                  << " | Ingenuo=" << std::setw(7) << std::setprecision(3) << t_ing << "ms"
                  << " | Lineal=" << std::setw(6) << t_lin << "ms"
                  << " | Speedup=" << std::setw(6) << std::setprecision(1) << speedup << "x"
                  << " | CutNodes=" << art_lin.size()
                  << " | Check=" << (ok ? "PASS" : "FAIL") << "\n";
    }
}

// ============================================================================
// E5: Simulación Aplicada del Token Pirata (Probabilidades Reales 2026)
// ============================================================================
void ejecutar_experimento_e5_token_pirata(const std::string& dir_grafos, const std::string& dir_csv) {
    std::cout << "\n[E5] Ejecutando simulacion aplicada del Token Pirata (Loot-Lobby-Repeat vs. Rotacion vs. Escuadron)...\n";

    fs::path ruta_comp = fs::path(dir_grafos) / "macro_poi_complete.graph";
    fs::path ruta_spar = fs::path(dir_grafos) / "macro_poi_sparse.graph";
    if (!fs::exists(ruta_comp) || !fs::exists(ruta_spar)) {
        std::cerr << "[AVISO] Faltan grafos macro para E5.\n";
        return;
    }

    GrafoCargado g_comp = cargar_grafo(ruta_comp.string());
    GrafoCargado g_spar = cargar_grafo(ruta_spar.string());
    int n = g_comp.lista.num_nodos();
    const auto& nodos = g_comp.lista.nodos();

    // Matriz de tiempos mínimos reales entre POIs sobre la red escasa de caminos
    ResultadoFloyd fl = floyd(g_spar.matriz);

    // Ordenar POIs por número de cofres descendente
    std::vector<int> pois_por_cofres(static_cast<size_t>(n));
    std::iota(pois_por_cofres.begin(), pois_por_cofres.end(), 0);
    std::sort(pois_por_cofres.begin(), pois_por_cofres.end(), [&](int a, int b) {
        return nodos[a].cofres > nodos[b].cofres;
    });

    // TSP macro completo (todos los POIs)
    ResultadoTSP tsp_macro = tsp_exacto_backtracking(g_comp.matriz, 10.0);
    int total_cofres_pois = 0;
    double total_saqueo_pois = 0.0;
    for (const auto& nd : nodos) {
        total_cofres_pois += nd.cofres;
        total_saqueo_pois += nd.tiempo_saqueo;
    }

    // Particionado MST en 4 escuadrones sobre macro_poi_complete
    ResultadoMST mst_macro = mst_kruskal(g_comp.lista);
    auto clusters_4 = particionar_escuadron_mst(g_comp.lista, mst_macro, 4);

    // Tiempo de ruta abierta + saqueo de cada uno de los 4 jugadores en su clúster MST
    double max_tiempo_cluster_mst = 0.0;
    int cofres_squad_mst = 0;
    for (const auto& cl : clusters_4) {
        GrafoCargado sub = construir_subgrafo_completo(g_comp.matriz, cl.nodos, "cluster");
        ResultadoTSP r_cl = tsp_exacto_backtracking(sub.matriz, 5.0);
        double t_jugador = r_cl.coste_abierto + cl.tiempo_saqueo_total;
        max_tiempo_cluster_mst = std::max(max_tiempo_cluster_mst, t_jugador);
        cofres_squad_mst += cl.total_cofres;
    }

    // Probabilidades oficiales del evento Treasure Hunters (noviembre 2026)
    struct ModoEvento {
        std::string nombre;
        double p;
    };
    std::vector<ModoEvento> modos = {
        {"Normal_1_en_137500", 1.0 / 137500.0},
        {"TreasureHours2x_1_en_68750", 1.0 / 68750.0}
    };

    std::ofstream f_sim(fs::path(dir_csv) / "e5_token_simulation.csv");
    f_sim << "estrategia,jugadores,modo_evento,t_lobby_s,cofres_por_partida,tiempo_partida_s,"
             "cofres_por_hora,horas_esperadas_media,horas_p50,horas_p90,detalle\n";
    f_sim << std::fixed << std::setprecision(3);

    auto registrar = [&](const std::string& est,
                         int jugadores,
                         double t_lobby,
                         int cofres_partida,
                         double tiempo_activo_s,
                         const std::string& detalle) {
        double t_partida = t_lobby + tiempo_activo_s;
        double cofres_hora = (cofres_partida / t_partida) * 3600.0;

        for (const auto& modo : modos) {
            double k_media = 1.0 / modo.p;
            double k_p50 = std::log(1.0 - 0.50) / std::log(1.0 - modo.p);
            double k_p90 = std::log(1.0 - 0.90) / std::log(1.0 - modo.p);

            f_sim << est << "," << jugadores << "," << modo.nombre << ","
                  << t_lobby << "," << cofres_partida << "," << t_partida << ","
                  << cofres_hora << "," << (k_media / cofres_hora) << ","
                  << (k_p50 / cofres_hora) << "," << (k_p90 / cofres_hora) << ","
                  << detalle << "\n";
        }
    };

    for (double t_lobby : {60.0, 90.0, 120.0}) {
        // Estrategia 1: Solo Loot-Lobby-Repeat en el POI más rentable para este t_lobby
        int mejor_poi = pois_por_cofres[0];
        double mejor_tasa = -1.0;
        for (int i = 0; i < n; ++i) {
            if (nodos[i].cofres <= 0) {
                continue;
            }
            double tasa = nodos[i].cofres / (t_lobby + nodos[i].tiempo_saqueo);
            if (tasa > mejor_tasa) {
                mejor_tasa = tasa;
                mejor_poi = i;
            }
        }
        registrar("Solo_Loot_Lobby_Repeat_1POI", 1, t_lobby,
                  nodos[mejor_poi].cofres, nodos[mejor_poi].tiempo_saqueo,
                  nodos[mejor_poi].etiqueta);

        // Estrategia 2: Solo Rotación Top-3 POIs más densos (ruta abierta óptima con Floyd)
        std::vector<int> top3(pois_por_cofres.begin(), pois_por_cofres.begin() + std::min(3, n));
        int cofres_top3 = 0;
        double saqueo_top3 = 0.0;
        for (int id : top3) {
            cofres_top3 += nodos[id].cofres;
            saqueo_top3 += nodos[id].tiempo_saqueo;
        }
        // Mejor ordenación abierta entre los 3 POIs usando distancias reales de Floyd
        std::sort(top3.begin(), top3.end());
        double mejor_viaje_top3 = INF;
        do {
            double v = 0.0;
            for (size_t i = 0; i + 1 < top3.size(); ++i) {
                v += fl.dist(top3[i], top3[i + 1]);
            }
            mejor_viaje_top3 = std::min(mejor_viaje_top3, v);
        } while (std::next_permutation(top3.begin(), top3.end()));

        registrar("Solo_Rotacion_Top3_POIs", 1, t_lobby,
                  cofres_top3, saqueo_top3 + mejor_viaje_top3, "Top3_POIs_Floyd");

        // Estrategia 3: Solo Rotación Isla Completa (TSP exacto abierto)
        registrar("Solo_Rotacion_Completa_TSP", 1, t_lobby,
                  total_cofres_pois, total_saqueo_pois + tsp_macro.coste_abierto, "16_POIs_TSP");

        // Estrategia 4: Escuadrón 4 jugadores SIN coordinación (todos caen en el mismo POI)
        // Asumimos factor de paralelismo 2.8x por solapamiento/colisiones dentro del mismo POI
        registrar("Squad4_Sin_Coordinacion_1POI", 4, t_lobby,
                  nodos[mejor_poi].cofres, nodos[mejor_poi].tiempo_saqueo / 2.8,
                  "4_en_" + nodos[mejor_poi].etiqueta);

        // Estrategia 5: Escuadrón 4 jugadores coordinado — Top-4 POIs disjuntos + Lobby Repeat
        int cofres_top4 = 0;
        double max_saqueo_top4 = 0.0;
        for (int i = 0; i < std::min(4, n); ++i) {
            int id = pois_por_cofres[i];
            cofres_top4 += nodos[id].cofres;
            max_saqueo_top4 = std::max(max_saqueo_top4, nodos[id].tiempo_saqueo);
        }
        registrar("Squad4_Top4_POIs_Repeat", 4, t_lobby,
                  cofres_top4, max_saqueo_top4, "4_POIs_Disjuntos");

        // Estrategia 6: Escuadrón 4 jugadores coordinado por Particionado MST (Kruskal)
        registrar("Squad4_Particionado_MST_Isla", 4, t_lobby,
                  cofres_squad_mst, max_tiempo_cluster_mst, "4_Clusters_MST");
    }

    std::cout << "  - Simulacion exportada a results/csv/e5_token_simulation.csv\n";
    std::cout << "  - Mejor POI individual (t_lobby=90s): " << nodos[pois_por_cofres[0]].etiqueta
              << " (" << nodos[pois_por_cofres[0]].cofres << " cofres)\n";
    std::cout << "  - Escuadron 4 (Particionado MST): " << cofres_squad_mst
              << " cofres totales en " << std::fixed << std::setprecision(1)
              << max_tiempo_cluster_mst << " s de juego activo por partida\n";
}

}  // namespace aed1