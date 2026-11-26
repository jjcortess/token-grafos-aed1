#include "graph.hpp"

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <stdexcept>

namespace aed1 {

GrafoMatriz::GrafoMatriz(int n, bool dirigido, std::vector<Nodo> nodos)
    : n_(n),
      m_(0),
      dirigido_(dirigido),
      nodos_(std::move(nodos)),
      mat_(static_cast<size_t>(n) * static_cast<size_t>(n), INF) {
    for (int i = 0; i < n_; ++i) {
        mat_[static_cast<size_t>(i) * static_cast<size_t>(n_) + static_cast<size_t>(i)] = 0.0;
    }
}

void GrafoMatriz::insertar_arista(int u, int v, double peso) {
    if (u < 0 || u >= n_ || v < 0 || v >= n_ || u == v) {
        return;
    }
    size_t idx_uv = static_cast<size_t>(u) * static_cast<size_t>(n_) + static_cast<size_t>(v);
    bool era_nueva = !std::isfinite(mat_[idx_uv]);
    if (peso < mat_[idx_uv]) {
        mat_[idx_uv] = peso;
    }
    if (!dirigido_) {
        size_t idx_vu = static_cast<size_t>(v) * static_cast<size_t>(n_) + static_cast<size_t>(u);
        if (peso < mat_[idx_vu]) {
            mat_[idx_vu] = peso;
        }
    }
    if (era_nueva) {
        ++m_;
    }
}

bool GrafoMatriz::existe_arista(int u, int v) const {
    return u != v && std::isfinite(coste(u, v));
}

size_t GrafoMatriz::memoria_bytes() const {
    return sizeof(*this) + mat_.capacity() * sizeof(double);
}

GrafoLista::GrafoLista(int n, bool dirigido, std::vector<Nodo> nodos)
    : n_(n), dirigido_(dirigido), nodos_(std::move(nodos)), adj_(static_cast<size_t>(n)) {}

void GrafoLista::insertar_arista(const Arista& arista) {
    if (arista.u < 0 || arista.u >= n_ || arista.v < 0 || arista.v >= n_ || arista.u == arista.v) {
        return;
    }
    aristas_.push_back(arista);
    adj_[arista.u].push_back({arista.v, arista.peso});
    if (!dirigido_) {
        adj_[arista.v].push_back({arista.u, arista.peso});
    }
}

size_t GrafoLista::memoria_bytes() const {
    size_t total = sizeof(*this) + adj_.capacity() * sizeof(std::vector<Adyacente>);
    for (const auto& lista_v : adj_) {
        total += lista_v.capacity() * sizeof(Adyacente);
    }
    return total;
}

GrafoCargado cargar_grafo(const std::string& ruta_fichero) {
    std::ifstream in(ruta_fichero);
    if (!in.is_open()) {
        throw std::runtime_error("No se pudo abrir el fichero de grafo: " + ruta_fichero);
    }

    int n = 0;
    int m = 0;
    int dir_flag = 0;
    if (!(in >> n >> m >> dir_flag)) {
        throw std::runtime_error("Cabecera inválida en: " + ruta_fichero);
    }
    bool dirigido = (dir_flag != 0);

    std::vector<Nodo> nodos(static_cast<size_t>(n));
    for (int i = 0; i < n; ++i) {
        Nodo nd;
        if (!(in >> nd.id >> nd.x_m >> nd.y_m >> nd.cofres >> nd.tiempo_saqueo >> nd.etiqueta)) {
            throw std::runtime_error("Error leyendo nodo " + std::to_string(i) + " en " + ruta_fichero);
        }
        if (nd.id < 0 || nd.id >= n) {
            throw std::runtime_error("ID de nodo fuera de rango en " + ruta_fichero);
        }
        nodos[static_cast<size_t>(nd.id)] = nd;
    }

    GrafoCargado resultado;
    resultado.nombre = std::filesystem::path(ruta_fichero).stem().string();
    resultado.lista = GrafoLista(n, dirigido, nodos);
    resultado.matriz = GrafoMatriz(n, dirigido, nodos);

    for (int i = 0; i < m; ++i) {
        Arista a;
        if (!(in >> a.u >> a.v >> a.peso >> a.dist_m >> a.factor)) {
            throw std::runtime_error("Error leyendo arista " + std::to_string(i) + " en " + ruta_fichero);
        }
        resultado.lista.insertar_arista(a);
        resultado.matriz.insertar_arista(a.u, a.v, a.peso);
    }

    return resultado;
}

}  // namespace aed1