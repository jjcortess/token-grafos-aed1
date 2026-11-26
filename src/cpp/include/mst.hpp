#ifndef AED1_MST_HPP
#define AED1_MST_HPP

#include "graph.hpp"

#include <vector>

namespace aed1 {

struct ResultadoMST {
    std::vector<Arista> aristas;
    double coste_total = 0.0;
    bool conexo = true;
};

// Estructura de relaciones de equivalencia con punteros al padre (Tema 4.3.2.2)
class RelacionEquivalencia {
public:
    explicit RelacionEquivalencia(int n);

    int encuentra(int x);
    bool unir(int a, int b);

private:
    std::vector<int> padre_;
    std::vector<int> rango_;
};

// Algoritmo de Prim con arrays MAS_CERCANO y MENOR_COSTE sobre matriz: O(n^2)
ResultadoMST mst_prim(const GrafoMatriz& g);

// Algoritmo de Kruskal con ordenación de aristas + RelacionEquivalencia: O(a log a)
ResultadoMST mst_kruskal(const GrafoLista& g);

// Clúster asignado a cada jugador de un escuadrón al cortar las (k-1) aristas más largas del MST
struct ClusterEscuadron {
    int cluster_id = 0;
    std::vector<int> nodos;
    int total_cofres = 0;
    double coste_mst_interno = 0.0;
    double tiempo_saqueo_total = 0.0;
};

std::vector<ClusterEscuadron> particionar_escuadron_mst(const GrafoLista& g,
                                                        const ResultadoMST& mst,
                                                        int num_jugadores = 4);

}  // namespace aed1

#endif  // AED1_MST_HPP