#include "traversals.hpp"

#include <queue>

namespace aed1 {

namespace {

constexpr int NO_VISITADO = -2;
constexpr int RAIZ = -1;

// Procedimiento recursivo bpp(v) visto en teoría (Tema 4.3.1.1)
void bpp_rec(const GrafoLista& g,
             int v,
             int id_comp,
             int nodo_prohibido,
             ResultadoBPP& res) {
    res.componente[v] = id_comp;
    res.orden_visita.push_back(v);

    for (const auto& ady : g.adyacentes(v)) {
        int w = ady.destino;
        if (w == nodo_prohibido) {
            continue;
        }
        if (res.padre[w] == NO_VISITADO) {
            res.padre[w] = v;
            bpp_rec(g, w, id_comp, nodo_prohibido, res);
        } else if (!g.es_dirigido() && w != res.padre[v]) {
            // En grafo no dirigido, un arco hacia un nodo ya visitado que no es el padre implica ciclo
            res.tiene_ciclo = true;
        }
    }
}

void bpp_preorden_rec(const std::vector<std::vector<int>>& adj,
                      int v,
                      std::vector<bool>& visitado,
                      std::vector<int>& preorden) {
    visitado[v] = true;
    preorden.push_back(v);
    for (int w : adj[v]) {
        if (!visitado[w]) {
            bpp_preorden_rec(adj, w, visitado, preorden);
        }
    }
}

}  // namespace

ResultadoBPP busqueda_primero_profundidad(const GrafoLista& g, int nodo_prohibido) {
    int n = g.num_nodos();
    ResultadoBPP res;
    res.padre.assign(static_cast<size_t>(n), NO_VISITADO);
    res.componente.assign(static_cast<size_t>(n), -1);
    res.orden_visita.reserve(static_cast<size_t>(n));

    for (int v = 0; v < n; ++v) {
        if (v == nodo_prohibido || res.padre[v] != NO_VISITADO) {
            continue;
        }
        res.padre[v] = RAIZ;
        bpp_rec(g, v, res.num_componentes, nodo_prohibido, res);
        ++res.num_componentes;
    }

    return res;
}

std::vector<int> bpp_preorden_subgrafo(const std::vector<std::vector<int>>& adj, int inicio) {
    std::vector<bool> visitado(adj.size(), false);
    std::vector<int> preorden;
    preorden.reserve(adj.size());
    if (inicio >= 0 && static_cast<size_t>(inicio) < adj.size()) {
        bpp_preorden_rec(adj, inicio, visitado, preorden);
    }
    return preorden;
}

ResultadoBPA busqueda_primero_anchura(const GrafoLista& g, int origen, int max_saltos) {
    int n = g.num_nodos();
    ResultadoBPA res;
    res.padre.assign(static_cast<size_t>(n), NO_VISITADO);
    res.dist_saltos.assign(static_cast<size_t>(n), -1);

    if (origen < 0 || origen >= n) {
        return res;
    }

    std::queue<int> cola;
    res.padre[origen] = RAIZ;
    res.dist_saltos[origen] = 0;
    cola.push(origen);

    const auto& nodos = g.nodos();

    while (!cola.empty()) {
        int x = cola.front();
        cola.pop();

        ++res.nodos_alcanzados;
        res.cofres_alcanzados += nodos[static_cast<size_t>(x)].cofres;

        if (max_saltos >= 0 && res.dist_saltos[x] >= max_saltos) {
            continue;
        }

        for (const auto& ady : g.adyacentes(x)) {
            int y = ady.destino;
            if (res.padre[y] == NO_VISITADO) {
                res.padre[y] = x;
                res.dist_saltos[y] = res.dist_saltos[x] + 1;
                cola.push(y);
            }
        }
    }

    return res;
}

}  // namespace aed1