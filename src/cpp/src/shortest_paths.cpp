#include "shortest_paths.hpp"

#include <algorithm>
#include <cmath>
#include <functional>
#include <queue>
#include <utility>

namespace aed1 {

// Implementación fiel a las diapositivas 58-59 del Tema 4.3.3.1
ResultadoDijkstra dijkstra_matriz(const GrafoMatriz& g, int origen) {
    int n = g.num_nodos();
    ResultadoDijkstra res;
    res.D.assign(static_cast<size_t>(n), INF);
    res.P.assign(static_cast<size_t>(n), -1);
    std::vector<bool> S(static_cast<size_t>(n), false);

    // Inicialización desde el origen
    S[origen] = true;
    res.D[origen] = 0.0;
    for (int v = 0; v < n; ++v) {
        if (v == origen) {
            continue;
        }
        double c = g.coste(origen, v);
        if (std::isfinite(c)) {
            res.D[v] = c;
            res.P[v] = origen;
        }
    }

    // Repetir n - 1 veces: escoger v de T con mínimo D[v] y relajar candidatos
    for (int iter = 1; iter < n; ++iter) {
        int v_sel = -1;
        double min_d = INF;
        for (int v = 0; v < n; ++v) {
            if (!S[v] && res.D[v] < min_d) {
                min_d = res.D[v];
                v_sel = v;
            }
        }
        if (v_sel == -1 || !std::isfinite(min_d)) {
            break;  // El resto de vértices no son alcanzables
        }
        S[v_sel] = true;

        for (int w = 0; w < n; ++w) {
            if (!S[w]) {
                double c_vw = g.coste(v_sel, w);
                if (std::isfinite(c_vw) && res.D[v_sel] + c_vw < res.D[w]) {
                    res.D[w] = res.D[v_sel] + c_vw;
                    res.P[w] = v_sel;
                }
            }
        }
    }

    return res;
}

// Implementación optimizada con listas y cola de prioridad (diapositiva 61): O(a log n)
ResultadoDijkstra dijkstra_lista(const GrafoLista& g, int origen) {
    int n = g.num_nodos();
    ResultadoDijkstra res;
    res.D.assign(static_cast<size_t>(n), INF);
    res.P.assign(static_cast<size_t>(n), -1);
    std::vector<bool> S(static_cast<size_t>(n), false);

    using Par = std::pair<double, int>;
    std::priority_queue<Par, std::vector<Par>, std::greater<Par>> pq;

    res.D[origen] = 0.0;
    pq.push({0.0, origen});

    while (!pq.empty()) {
        auto [dist_v, v] = pq.top();
        pq.pop();

        if (S[v]) {
            continue;  // Entrada obsoleta en el montículo
        }
        S[v] = true;

        for (const auto& ady : g.adyacentes(v)) {
            int w = ady.destino;
            if (!S[w] && dist_v + ady.peso < res.D[w]) {
                res.D[w] = dist_v + ady.peso;
                res.P[w] = v;
                pq.push({res.D[w], w});
            }
        }
    }

    return res;
}

std::vector<int> reconstruir_camino_dijkstra(int origen, int destino, const std::vector<int>& P) {
    std::vector<int> camino;
    if (destino < 0 || destino >= static_cast<int>(P.size())) {
        return camino;
    }
    int actual = destino;
    while (actual != -1 && actual != origen) {
        camino.push_back(actual);
        actual = P[actual];
    }
    if (actual != origen) {
        return {};  // No existe camino
    }
    camino.push_back(origen);
    std::reverse(camino.begin(), camino.end());
    return camino;
}

// Implementación fiel a las diapositivas 66-67 del Tema 4.3.3.2
ResultadoFloyd floyd(const GrafoMatriz& g) {
    int n = g.num_nodos();
    ResultadoFloyd res;
    res.n = n;
    res.D.resize(static_cast<size_t>(n) * static_cast<size_t>(n));
    res.P.assign(static_cast<size_t>(n) * static_cast<size_t>(n), -1);

    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            res.D[static_cast<size_t>(i) * static_cast<size_t>(n) + static_cast<size_t>(j)] = g.coste(i, j);
        }
    }

    for (int k = 0; k < n; ++k) {
        size_t fila_k = static_cast<size_t>(k) * static_cast<size_t>(n);
        for (int i = 0; i < n; ++i) {
            size_t fila_i = static_cast<size_t>(i) * static_cast<size_t>(n);
            double d_ik = res.D[fila_i + static_cast<size_t>(k)];
            if (!std::isfinite(d_ik)) {
                continue;
            }
            for (int j = 0; j < n; ++j) {
                double d_kj = res.D[fila_k + static_cast<size_t>(j)];
                if (std::isfinite(d_kj) && d_ik + d_kj < res.D[fila_i + static_cast<size_t>(j)]) {
                    res.D[fila_i + static_cast<size_t>(j)] = d_ik + d_kj;
                    res.P[fila_i + static_cast<size_t>(j)] = k;
                }
            }
        }
    }

    return res;
}

namespace {

void camino_floyd_rec(int i, int j, const ResultadoFloyd& f, std::vector<int>& ruta) {
    int k = f.pivote(i, j);
    if (k != -1) {
        camino_floyd_rec(i, k, f, ruta);
        ruta.push_back(k);
        camino_floyd_rec(k, j, f, ruta);
    }
}

}  // namespace

std::vector<int> reconstruir_camino_floyd(int i, int j, const ResultadoFloyd& f) {
    if (!std::isfinite(f.dist(i, j))) {
        return {};
    }
    std::vector<int> ruta;
    ruta.push_back(i);
    if (i != j) {
        camino_floyd_rec(i, j, f, ruta);
        ruta.push_back(j);
    }
    return ruta;
}

}  // namespace aed1