#include "experiments.hpp"

#include <filesystem>
#include <iostream>
#include <string>

namespace fs = std::filesystem;

int main(int argc, char* argv[]) {
    std::string modo = (argc >= 2) ? argv[1] : "all";
    std::string dir_grafos = (argc >= 3) ? argv[2] : "data/processed";
    std::string dir_csv = (argc >= 4) ? argv[3] : "results/csv";

    try {
        fs::create_directories(dir_csv);

        std::cout << "====================================================================\n";
        std::cout << "  AED1 - Tema 4 (Grafos) | Nucleo Algoritmico C++17 (Token Pirata)\n";
        std::cout << "  Grafos: " << dir_grafos << "  |  Salida CSV: " << dir_csv << "\n";
        std::cout << "====================================================================\n";

        if (modo == "all" || modo == "e1") {
            aed1::ejecutar_experimento_e1_tsp(dir_grafos, dir_csv);
        }
        if (modo == "all" || modo == "e2") {
            aed1::ejecutar_experimento_e2_caminos(dir_grafos, dir_csv);
        }
        if (modo == "all" || modo == "e3") {
            aed1::ejecutar_experimento_e3_mst_escuadron(dir_grafos, dir_csv);
        }
        if (modo == "all" || modo == "e4") {
            aed1::ejecutar_experimento_e4_articulacion(dir_grafos, dir_csv);
        }
        if (modo == "all" || modo == "e5") {
            aed1::ejecutar_experimento_e5_token_pirata(dir_grafos, dir_csv);
        }

        std::cout << "\n[OK] Ejecucion completada. CSVs generados en: " << dir_csv << "/\n";
        return 0;
    } catch (const std::exception& ex) {
        std::cerr << "\n[ERROR CRITICO] " << ex.what() << "\n";
        return 1;
    }
}