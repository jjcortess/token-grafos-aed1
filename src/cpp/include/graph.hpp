#ifndef AED1_GRAPH_HPP
#define AED1_GRAPH_HPP

#include <cstddef>
#include <limits>
#include <string>
#include <vector>

namespace aed1 {

constexpr double INF = std::numeric_limits<double>::infinity();

// Metadatos reales de cada vértice leídos desde los ficheros .graph
struct Nodo {
    int id = 0;
    double x_m = 0.0;
    double y_m = 0.0;
    int cofres = 0;
    double tiempo_saqueo = 0.0;
    std::string etiqueta;
};

// Arista ponderada (usada por Kruskal y exportación de resultados)
struct Arista {
    int u = 0;
    int v = 0;
    double peso = 0.0;       // segundos de desplazamiento
    double dist_m = 0.0;     // distancia euclídea en metros
    double factor = 1.0;     // penalización de terreno/puente
};

// Elemento de una lista de adyacencia: (vértice destino, coste)
struct Adyacente {
    int destino = 0;
    double peso = 0.0;
};

// ============================================================================
// Representación 4.2.1: Matriz de adyacencia (O(n^2) en memoria)
// ============================================================================
class GrafoMatriz {
public:
    GrafoMatriz() = default;
    GrafoMatriz(int n, bool dirigido, std::vector<Nodo> nodos);

    void insertar_arista(int u, int v, double peso);

    int num_nodos() const { return n_; }
    int num_aristas() const { return m_; }
    bool es_dirigido() const { return dirigido_; }
    const std::vector<Nodo>& nodos() const { return nodos_; }

    double coste(int u, int v) const {
        return mat_[static_cast<size_t>(u) * static_cast<size_t>(n_) + static_cast<size_t>(v)];
    }

    bool existe_arista(int u, int v) const;
    size_t memoria_bytes() const;

private:
    int n_ = 0;
    int m_ = 0;
    bool dirigido_ = false;
    std::vector<Nodo> nodos_;
    std::vector<double> mat_;  // Matriz plana n x n para localidad de caché
};

// ============================================================================
// Representación 4.2.2: Listas de adyacencia (O(n + a) en memoria)
// ============================================================================
class GrafoLista {
public:
    GrafoLista() = default;
    GrafoLista(int n, bool dirigido, std::vector<Nodo> nodos);

    void insertar_arista(const Arista& arista);

    int num_nodos() const { return n_; }
    int num_aristas() const { return static_cast<int>(aristas_.size()); }
    bool es_dirigido() const { return dirigido_; }
    const std::vector<Nodo>& nodos() const { return nodos_; }
    const std::vector<Adyacente>& adyacentes(int v) const { return adj_[v]; }
    const std::vector<Arista>& aristas() const { return aristas_; }

    size_t memoria_bytes() const;

private:
    int n_ = 0;
    bool dirigido_ = false;
    std::vector<Nodo> nodos_;
    std::vector<std::vector<Adyacente>> adj_;
    std::vector<Arista> aristas_;
};

// Contenedor que expone simultáneamente ambas representaciones para benchmarking
struct GrafoCargado {
    std::string nombre;
    GrafoLista lista;
    GrafoMatriz matriz;
};

// Carga un fichero .graph generado por src/python/02_build_graphs.py
GrafoCargado cargar_grafo(const std::string& ruta_fichero);

}  // namespace aed1

#endif  // AED1_GRAPH_HPP