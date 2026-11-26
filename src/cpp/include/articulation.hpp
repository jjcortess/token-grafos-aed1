#ifndef AED1_ARTICULATION_HPP
#define AED1_ARTICULATION_HPP

#include "graph.hpp"

#include <vector>

namespace aed1 {

// Algoritmo ingenuo (diapositiva 86): eliminar cada nodo v y comprobar conectividad con BPP -> O(n(n+a))
std::vector<int> puntos_articulacion_ingenuo(const GrafoLista& g);

// Algoritmo lineal en una sola BPP (diapositiva 87): vectores nbpp y bajo -> O(n+a)
std::vector<int> puntos_articulacion_lineal(const GrafoLista& g);

}  // namespace aed1

#endif  // AED1_ARTICULATION_HPP