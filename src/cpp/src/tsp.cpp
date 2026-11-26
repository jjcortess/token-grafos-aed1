#include "tsp.hpp"
#include "mst.hpp"
#include "traversals.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>

namespace aed1 {

void evaluar_ciclo(const GrafoMatriz& g, ResultadoTSP& res) {
    int n = static_cast<int>(res.ruta.size());
    if (n <= 1) {
        res.coste_ciclo = 0.0;
        res.coste_abierto = 0.0;
        return;
    }

    double suma = 0.0;
    double arista_max = 0.0;
    for (int i = 0; i < n; ++i) {
        int u = res.ruta[i];
        int v = res.ruta[(i + 1) % n];
        double c = g.coste(u, v);
        suma += c;
        if (c > arista_max) {
            arista_max = c;
        }
    }
    res.coste_ciclo = suma;
    res.coste_abierto = suma - arista_max;
}

ResultadoTSP tsp_vecino_mas_cercano(const GrafoMatriz& g, bool multi_inicio) {
    int n = g.num_nodos();
    ResultadoTSP mejor;
    if (n == 0) {
        return mejor;
    }

    int max_inicios = multi_inicio ? n : 1;
    for (int inicio = 0; inicio < max_inicios; ++inicio) {
        std::vector<bool> visitado(static_cast<size_t>(n), false);
        ResultadoTSP cand;
        cand.ruta.reserve(static_cast<size_t>(n));

        int actual = inicio;
        visitado[actual] = true;
        cand.ruta.push_back(actual);

        for (int paso = 1; paso < n; ++paso) {
            int sig = -1;
            double min_c = INF;
            for (int v = 0; v < n; ++v) {
                if (!visitado[v]) {
                    double c = g.coste(actual, v);
                    if (c < min_c) {
                        min_c = c;
                        sig = v;
                    }
                }
            }
            if (sig == -1) {
                break;
            }
            visitado[sig] = true;
            cand.ruta.push_back(sig);
            actual = sig;
        }

        evaluar_ciclo(g, cand);
        cand.estados_explorados = static_cast<long long>(n) * static_cast<long long>(n);
        if (cand.coste_ciclo < mejor.coste_ciclo) {
            mejor = std::move(cand);
        }
    }

    return mejor;
}

ResultadoTSP tsp_heuristica_mst_bpp(const GrafoLista& gl, const GrafoMatriz& gm) {
    int n = gl.num_nodos();
    ResultadoTSP res;
    if (n == 0) {
        return res;
    }

    // 1. Obtener el Árbol de Expansión Mínimo mediante Kruskal
    ResultadoMST mst = mst_kruskal(gl);

    // 2. Construir las listas de adyacencia del MST (ordenadas por coste para determinismo)
    std::vector<std::vector<int>> adj_mst(static_cast<size_t>(n));
    for (const auto& a : mst.aristas) {
        adj_mst[a.u].push_back(a.v);
        adj_mst[a.v].push_back(a.u);
    }

    // 3. Recorrido BPP en preorden desde el nodo 0 (atajando vértices ya visitados)
    res.ruta = bpp_preorden_subgrafo(adj_mst, 0);
    evaluar_ciclo(gm, res);
    res.estados_explorados = gl.num_aristas();
    return res;
}

namespace {

struct ContextoTSP {
    const GrafoMatriz& g;
    int n;
    std::vector<double> min_saliente;
    std::vector<std::vector<int>> vecinos_ordenados;
    std::vector<bool> visitado;
    std::vector<int> ruta_actual;
    std::vector<int> mejor_ruta;
    double mejor_coste = INF;
    long long estados = 0;
    bool abortado_tiempo = false;
    std::chrono::steady_clock::time_point limite_tiempo;
};

void backtrack_tsp(ContextoTSP& ctx, int nivel, double coste_actual, double suma_min_restante) {
    ++ctx.estados;

    // Comprobar límite de seguridad cada 16.384 estados para no afectar el rendimiento
    if ((ctx.estados & 16383LL) == 0 && std::chrono::steady_clock::now() >= ctx.limite_tiempo) {
        ctx.abortado_tiempo = true;
        return;
    }

    int actual = ctx.ruta_actual[nivel - 1];

    // Caso base: todos los vértices visitados -> cerrar ciclo regresando a 0
    if (nivel == ctx.n) {
        double total = coste_actual + ctx.g.coste(actual, 0);
        if (total < ctx.mejor_coste) {
            ctx.mejor_coste = total;
            ctx.mejor_ruta = ctx.ruta_actual;
        }
        return;
    }

    // Cota inferior admisible: al menos hay que salir de 'actual' y de cada nodo no visitado
    if (coste_actual + ctx.min_saliente[actual] + suma_min_restante >= ctx.mejor_coste - 1e-9) {
        return;
    }

    for (int sig : ctx.vecinos_ordenados[actual]) {
        if (ctx.visitado[sig]) {
            continue;
        }
        // Ruptura de simetría en grafos no dirigidos: evita recorrer cada ciclo en los dos sentidos
        if (nivel == ctx.n - 1 && ctx.n >= 3 && sig < ctx.ruta_actual[1]) {
            continue;
        }

        double nuevo_coste = coste_actual + ctx.g.coste(actual, sig);
        double nueva_suma_min = suma_min_restante - ctx.min_saliente[sig];

        if (nuevo_coste + ctx.min_saliente[sig] + nueva_suma_min >= ctx.mejor_coste - 1e-9) {
            continue;
        }

        ctx.visitado[sig] = true;
        ctx.ruta_actual[nivel] = sig;
        backtrack_tsp(ctx, nivel + 1, nuevo_coste, nueva_suma_min);
        ctx.visitado[sig] = false;

        if (ctx.abortado_tiempo) {
            return;
        }
    }
}

}  // namespace

ResultadoTSP tsp_exacto_backtracking(const GrafoMatriz& g, double timeout_seg) {
    int n = g.num_nodos();
    ResultadoTSP res;
    if (n <= 1) {
        if (n == 1) {
            res.ruta = {0};
        }
        res.coste_ciclo = 0.0;
        res.coste_abierto = 0.0;
        res.optimo_garantizado = true;
        return res;
    }

    // Inicializamos la cota superior con Vecino Más Cercano para acelerar la poda sin perder exactitud
    ResultadoTSP cota_inicial = tsp_vecino_mas_cercano(g, true);

    ContextoTSP ctx{
        g,
        n,
        std::vector<double>(static_cast<size_t>(n), INF),
        std::vector<std::vector<int>>(static_cast<size_t>(n)),
        std::vector<bool>(static_cast<size_t>(n), false),
        std::vector<int>(static_cast<size_t>(n), -1),
        cota_inicial.ruta,
        cota_inicial.coste_ciclo,
        0,
        false,
        std::chrono::steady_clock::now() +
            std::chrono::milliseconds(static_cast<long long>(timeout_seg * 1000.0))};

    // Precomputar la arista mínima saliente de cada vértice y vecinos ordenados por cercanía
    double suma_min_total = 0.0;
    for (int u = 0; u < n; ++u) {
        std::vector<std::pair<double, int>> vecs;
        vecs.reserve(static_cast<size_t>(n - 1));
        for (int v = 0; v < n; ++v) {
            if (u == v) {
                continue;
            }
            double c = g.coste(u, v);
            ctx.min_saliente[u] = std::min(ctx.min_saliente[u], c);
            vecs.push_back({c, v});
        }
        std::sort(vecs.begin(), vecs.end());
        ctx.vecinos_ordenados[u].reserve(vecs.size());
        for (const auto& [c, v] : vecs) {
            (void)c;
            ctx.vecinos_ordenados[u].push_back(v);
        }
        if (u != 0) {
            suma_min_total += ctx.min_saliente[u];
        }
    }

    ctx.visitado[0] = true;
    ctx.ruta_actual[0] = 0;
    backtrack_tsp(ctx, 1, 0.0, suma_min_total);

    res.ruta = std::move(ctx.mejor_ruta);
    evaluar_ciclo(g, res);
    res.estados_explorados = ctx.estados;
    res.optimo_garantizado = !ctx.abortado_tiempo;
    return res;
}

}  // namespace aed1