#ifndef AED1_SHORTEST_PATHS_HPP
#define AED1_SHORTEST_PATHS_HPP

#include "graph.hpp"

#include <vector>

namespace aed1 {

struct ResultadoDijkstra {
    std::vector<double> D;  // Costes mínimos desde el origen
    std::vector<int> P;     // Predecesor en el camino mínimo (-1 si no hay)
};

// Dijkstra clásico con matriz de adyacencia y búsqueda lineal: O(n^2)
ResultadoDijkstra dijkstra_matriz(const GrafoMatriz& g, int origen);

// Dijkstra optimizado con listas de adyacencia y cola de prioridad: O(a log n)
ResultadoDijkstra dijkstra_lista(const GrafoLista& g, int origen);

// Reconstruye el camino mínimo desde origen hasta destino a partir de P
std::vector<int> reconstruir_camino_dijkstra(int origen, int destino, const std::vector<int>& P);

// Resultado del algoritmo de Floyd entre todos los pares: O(n^3)
struct ResultadoFloyd {
    int n = 0;
    std::vector<double> D;  // Matriz plana n x n de costes mínimos
    std::vector<int> P;     // Matriz plana n x n de pivotes intermedios (-1 = directo)

    double dist(int i, int j) const {
        return D[static_cast<size_t>(i) * static_cast<size_t>(n) + static_cast<size_t>(j)];
    }
    int pivote(int i, int j) const {
        return P[static_cast<size_t>(i) * static_cast<size_t>(n) + static_cast<size_t>(j)];
    }
};

ResultadoFloyd floyd(const GrafoMatriz& g);

// Recuperación recursiva del camino mínimo según el procedimiento camino(i, j) del Tema 4.3.3.2
std::vector<int> reconstruir_camino_floyd(int i, int j, const ResultadoFloyd& f);

}  // namespace aed1

#endif  // AED1_SHORTEST_PATHS_HPP