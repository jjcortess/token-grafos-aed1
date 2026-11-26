#include "articulation.hpp"
#include "traversals.hpp"

#include <algorithm>

namespace aed1 {

std::vector<int> puntos_articulacion_ingenuo(const GrafoLista& g) {
    int n = g.num_nodos();
    int comp_base = busqueda_primero_profundidad(g).num_componentes;

    std::vector<int> puntos;
    for (int v = 0; v < n; ++v) {
        int comp_sin_v = busqueda_primero_profundidad(g, v).num_componentes;
        if (comp_sin_v > comp_base) {
            puntos.push_back(v);
        }
    }
    return puntos;
}

namespace {

// BPP recursiva que calcula nbpp[v] y bajo[v] según la fórmula de la diapositiva 87
void art_bpp(const GrafoLista& g,
             int v,
             int padre,
             int& contador_bpp,
             std::vector<int>& nbpp,
             std::vector<int>& bajo,
             std::vector<bool>& es_art) {
    nbpp[v] = ++contador_bpp;
    bajo[v] = nbpp[v];
    int hijos_en_arbol = 0;

    for (const auto& ady : g.adyacentes(v)) {
        int w = ady.destino;
        if (w == padre) {
            continue;
        }
        if (nbpp[w] == 0) {
            // Arco del árbol de expansión
            ++hijos_en_arbol;
            art_bpp(g, w, v, contador_bpp, nbpp, bajo, es_art);
            bajo[v] = std::min(bajo[v], bajo[w]);

            // Condición 4 (nodo no raíz): tiene algún hijo w con bajo[w] >= nbpp[v]
            if (padre != -1 && bajo[w] >= nbpp[v]) {
                es_art[v] = true;
            }
        } else {
            // Arco de retroceso (v, w)
            bajo[v] = std::min(bajo[v], nbpp[w]);
        }
    }

    // Condición 3 (raíz): tiene 2 o más hijos en el árbol de expansión
    if (padre == -1 && hijos_en_arbol >= 2) {
        es_art[v] = true;
    }
}

}  // namespace

std::vector<int> puntos_articulacion_lineal(const GrafoLista& g) {
    int n = g.num_nodos();
    std::vector<int> nbpp(static_cast<size_t>(n), 0);
    std::vector<int> bajo(static_cast<size_t>(n), 0);
    std::vector<bool> es_art(static_cast<size_t>(n), false);

    int contador = 0;
    for (int v = 0; v < n; ++v) {
        if (nbpp[v] == 0) {
            art_bpp(g, v, -1, contador, nbpp, bajo, es_art);
        }
    }

    std::vector<int> puntos;
    for (int v = 0; v < n; ++v) {
        if (es_art[v]) {
            puntos.push_back(v);
        }
    }
    return puntos;
}

}  // namespace aed1