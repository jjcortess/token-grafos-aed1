#ifndef AED1_TSP_HPP
#define AED1_TSP_HPP

#include "graph.hpp"

#include <vector>

namespace aed1 {

struct ResultadoTSP {
    std::vector<int> ruta;          // Orden de visita de los n vértices
    double coste_ciclo = INF;       // Coste del ciclo cerrado completo (TSP clásico)
    double coste_abierto = INF;     // Coste sin volver al origen (quitando la arista más larga)
    bool optimo_garantizado = false;
    long long estados_explorados = 0;
};

// Evalúa un ciclo dado y calcula tanto su coste cerrado como su mejor ruta abierta
void evaluar_ciclo(const GrafoMatriz& g, ResultadoTSP& res);

// Heurística 1: Vecino Más Cercano (con opción de probar todos los nodos de inicio)
ResultadoTSP tsp_vecino_mas_cercano(const GrafoMatriz& g, bool multi_inicio = true);

// Heurística 2: MST (Kruskal) + recorrido en preorden (BPP) — 2-aproximación métrica
ResultadoTSP tsp_heuristica_mst_bpp(const GrafoLista& gl, const GrafoMatriz& gm);

// Algoritmo exacto: búsqueda exhaustiva con backtracking y poda admisible por cota inferior
// Permite comparar el crecimiento exponencial (diapositivas 100-102) frente a las heurísticas.
ResultadoTSP tsp_exacto_backtracking(const GrafoMatriz& g, double timeout_seg = 12.0);

}  // namespace aed1

#endif  // AED1_TSP_HPP