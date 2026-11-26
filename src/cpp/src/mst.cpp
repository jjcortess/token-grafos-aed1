#include "mst.hpp"

#include <algorithm>
#include <cmath>
#include <queue>

namespace aed1 {

RelacionEquivalencia::RelacionEquivalencia(int n)
    : padre_(static_cast<size_t>(n)), rango_(static_cast<size_t>(n), 0) {
    for (int i = 0; i < n; ++i) {
        padre_[static_cast<size_t>(i)] = i;
    }
}

int RelacionEquivalencia::encuentra(int x) {
    if (padre_[x] != x) {
        padre_[x] = encuentra(padre_[x]);  // Compresión de caminos
    }
    return padre_[x];
}

bool RelacionEquivalencia::unir(int a, int b) {
    int ra = encuentra(a);
    int rb = encuentra(b);
    if (ra == rb) {
        return false;  // Ya están en el mismo componente conexo (formaría ciclo)
    }
    if (rango_[ra] < rango_[rb]) {
        padre_[ra] = rb;
    } else if (rango_[ra] > rango_[rb]) {
        padre_[rb] = ra;
    } else {
        padre_[rb] = ra;
        ++rango_[ra];
    }
    return true;
}

// Implementación fiel al esquema de Prim del Tema 4.3.2.1 (diapositiva 45)
ResultadoMST mst_prim(const GrafoMatriz& g) {
    int n = g.num_nodos();
    ResultadoMST res;
    if (n <= 1) {
        return res;
    }

    std::vector<int> mas_cercano(static_cast<size_t>(n), 0);
    std::vector<double> menor_coste(static_cast<size_t>(n), INF);
    std::vector<bool> en_solucion(static_cast<size_t>(n), false);

    // 1. Inicialmente U = {0}
    en_solucion[0] = true;
    for (int v = 1; v < n; ++v) {
        mas_cercano[v] = 0;
        menor_coste[v] = g.coste(0, v);
    }

    res.aristas.reserve(static_cast<size_t>(n - 1));

    // 2-4. Añadir los n - 1 vértices restantes
    for (int paso = 1; paso < n; ++paso) {
        int v_sel = -1;
        double min_val = INF;

        for (int v = 0; v < n; ++v) {
            if (!en_solucion[v] && menor_coste[v] < min_val) {
                min_val = menor_coste[v];
                v_sel = v;
            }
        }

        if (v_sel == -1 || !std::isfinite(min_val)) {
            res.conexo = false;
            break;
        }

        en_solucion[v_sel] = true;
        res.aristas.push_back({mas_cercano[v_sel], v_sel, min_val, 0.0, 1.0});
        res.coste_total += min_val;

        // Recalcular MAS_CERCANO y MENOR_COSTE para los nodos de V - U
        for (int w = 0; w < n; ++w) {
            if (!en_solucion[w]) {
                double c_vw = g.coste(v_sel, w);
                if (c_vw < menor_coste[w]) {
                    menor_coste[w] = c_vw;
                    mas_cercano[w] = v_sel;
                }
            }
        }
    }

    return res;
}

// Implementación fiel al esquema de Kruskal del Tema 4.3.2.2 (diapositivas 49-50)
ResultadoMST mst_kruskal(const GrafoLista& g) {
    int n = g.num_nodos();
    ResultadoMST res;
    if (n <= 1) {
        return res;
    }

    std::vector<Arista> ordenadas = g.aristas();
    std::sort(ordenadas.begin(), ordenadas.end(), [](const Arista& a, const Arista& b) {
        if (a.peso != b.peso) {
            return a.peso < b.peso;
        }
        return (a.u != b.u) ? (a.u < b.u) : (a.v < b.v);
    });

    RelacionEquivalencia conj(n);
    res.aristas.reserve(static_cast<size_t>(n - 1));

    for (const auto& arista : ordenadas) {
        if (conj.unir(arista.u, arista.v)) {
            res.aristas.push_back(arista);
            res.coste_total += arista.peso;
            if (static_cast<int>(res.aristas.size()) == n - 1) {
                break;
            }
        }
    }

    res.conexo = (static_cast<int>(res.aristas.size()) == n - 1);
    return res;
}

std::vector<ClusterEscuadron> particionar_escuadron_mst(const GrafoLista& g,
                                                        const ResultadoMST& mst,
                                                        int num_jugadores) {
    int n = g.num_nodos();
    if (n == 0 || num_jugadores <= 0) {
        return {};
    }

    // Ordenamos las aristas del MST de menor a mayor y eliminamos las (k - 1) más largas
    std::vector<Arista> aristas_cortadas = mst.aristas;
    std::sort(aristas_cortadas.begin(), aristas_cortadas.end(), [](const Arista& a, const Arista& b) {
        return a.peso < b.peso;
    });

    int cortes = std::min(num_jugadores - 1, static_cast<int>(aristas_cortadas.size()));
    aristas_cortadas.resize(aristas_cortadas.size() - static_cast<size_t>(cortes));

    // Construimos el bosque resultante y extraemos cada componente conexo
    std::vector<std::vector<std::pair<int, double>>> adj(static_cast<size_t>(n));
    for (const auto& a : aristas_cortadas) {
        adj[a.u].push_back({a.v, a.peso});
        adj[a.v].push_back({a.u, a.peso});
    }

    std::vector<bool> visitado(static_cast<size_t>(n), false);
    std::vector<ClusterEscuadron> clusters;
    const auto& nodos = g.nodos();

    for (int inicio = 0; inicio < n; ++inicio) {
        if (visitado[inicio]) {
            continue;
        }
        ClusterEscuadron cl;
        std::queue<int> q;
        visitado[inicio] = true;
        q.push(inicio);

        double suma_aristas_doble = 0.0;
        while (!q.empty()) {
            int u = q.front();
            q.pop();
            cl.nodos.push_back(u);
            cl.total_cofres += nodos[u].cofres;
            cl.tiempo_saqueo_total += nodos[u].tiempo_saqueo;

            for (const auto& [w, peso] : adj[u]) {
                suma_aristas_doble += peso;
                if (!visitado[w]) {
                    visitado[w] = true;
                    q.push(w);
                }
            }
        }
        cl.coste_mst_interno = suma_aristas_doble / 2.0;
        std::sort(cl.nodos.begin(), cl.nodos.end());
        clusters.push_back(std::move(cl));
    }

    // Ordenar clústeres de mayor a menor carga de cofres y numerar 0..k-1
    std::sort(clusters.begin(), clusters.end(), [](const ClusterEscuadron& a, const ClusterEscuadron& b) {
        return a.total_cofres > b.total_cofres;
    });
    for (size_t i = 0; i < clusters.size(); ++i) {
        clusters[i].cluster_id = static_cast<int>(i);
    }

    return clusters;
}

}  // namespace aed1