#ifndef AED1_EXPERIMENTS_HPP
#define AED1_EXPERIMENTS_HPP

#include <string>

namespace aed1 {

void ejecutar_experimento_e1_tsp(const std::string& dir_grafos, const std::string& dir_csv);
void ejecutar_experimento_e2_caminos(const std::string& dir_grafos, const std::string& dir_csv);
void ejecutar_experimento_e3_mst_escuadron(const std::string& dir_grafos, const std::string& dir_csv);
void ejecutar_experimento_e4_articulacion(const std::string& dir_grafos, const std::string& dir_csv);
void ejecutar_experimento_e5_token_pirata(const std::string& dir_grafos, const std::string& dir_csv);

}  // namespace aed1

#endif  // AED1_EXPERIMENTS_HPP