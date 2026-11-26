# Optimización de Rutas y Particionado Multiagente sobre Grafos Espaciales
### Estudio Algorítmico Aplicado al Evento «Token Pirata» de Fortnite (2026)

![C++17](https://img.shields.io/badge/C%2B%2B-17%20(puro)-00599C?style=flat-square&logo=cplusplus)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python)
![AED1](https://img.shields.io/badge/UMU-AED1%20Tema%204%20(Grafos)-B91C1C?style=flat-square)
![Verificación](https://img.shields.io/badge/Verificaci%C3%B3n%20Cruzada-100%25%20PASS-16A34A?style=flat-square)

**Asignatura:** Algoritmos y Estructuras de Datos I (AED1) — Grado en Ingeniería Informática (Curso 2026/2027)  
**Centro:** Facultad de Informática, Universidad de Murcia  
**Autores:** Juan José Cortés Arnaldos · Raúl Sánchez Ayala  
**Memoria completa:** [`docs/memoria_aed1_t4.pdf`](docs/memoria_aed1_t4.pdf)

---

## Tabla de contenidos
1. [Descripción y objetivo](#1-descripción-y-objetivo)
2. [Datasets reales y reproducibilidad](#2-datasets-reales-y-reproducibilidad)
3. [Algoritmos implementados en C++17](#3-algoritmos-implementados-en-c17)
4. [Estructura del repositorio](#4-estructura-del-repositorio)
5. [Guía de compilación y ejecución](#5-guía-de-compilación-y-ejecución)
6. [Resultados experimentales destacados](#6-resultados-experimentales-destacados)
7. [Reparto de tareas y uso de IA](#7-reparto-de-tareas-y-uso-de-ia)

---

## 1. Descripción y objetivo

Durante la minitemporada *Cazatesoros (Treasure Hunters)* de noviembre–diciembre de 2026, obtener el **Token Pirata (*Pirate Shop Access Token*)** en el mapa **Crossbones Isle** responde a ensayos de Bernoulli independientes por cada cofre abierto ($p = \frac{1}{137\,500}$ en modo normal y $p = \frac{1}{68\,750}$ en *Treasure Hours* $2\times$). Al ser la probabilidad idéntica en cualquier cofre, maximizar las probabilidades de éxito equivale a **maximizar la tasa de cofres abiertos por hora**.

Este proyecto modela *Crossbones Isle* como una familia de grafos espaciales ponderados por tiempo real de desplazamiento y saqueo para: