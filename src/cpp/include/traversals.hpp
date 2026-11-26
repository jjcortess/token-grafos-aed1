#ifndef AED1_TRAVERSALS_HPP
#define AED1_TRAVERSALS_HPP

#include "graph.hpp"

#include <vector>

namespace aed1 {

// Resultado de la Búsqueda Primero en Profundidad (BPP)
// padre[v]: -2 = noVisitado, -1 = raíz de un árbol del bosque, >=0 = padre de v
struct ResultadoBPP {
    std::vector<int> padre;
    std::vector<int> componente;
    std::vector<int> orden_visita;
    int num_componentes = 0;
    bool tiene_ciclo = false;
};

// Resultado de la Búsqueda Primero en Anchura (BPA) desde un nodo origen
struct ResultadoBPA {
    std::vector<int> padre;
    std::vector<int> dist_saltos;  // -1 si no es alcanzable dentro del límite
    int nodos_alcanzados = 0;
    int cofres_alcanzados = 0;
};

// BPP completa sobre todo el grafo (permite ignorar un nodo para análisis de fallos)
ResultadoBPP busqueda_primero_profundidad(const GrafoLista& g, int nodo_prohibido = -1);

// BPP en preorden desde una raíz sobre un subgrafo dado por listas de adyacencia (usada en TSP MST+BPP)
std::vector<int> bpp_preorden_subgrafo(const std::vector<std::vector<int>>& adj, int inicio);

// BPA con cola desde un nodo origen (si max_saltos >= 0, limita el alcance a k saltos)
ResultadoBPA busqueda_primero_anchura(const GrafoLista& g, int origen, int max_saltos = -1);

}  // namespace aed1

#endif  // AED1_TRAVERSALS_HPP