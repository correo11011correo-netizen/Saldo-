# 🚀 Crypto Hunter Pro v5.2 (Offline Search Engine)

Este repositorio contiene herramientas de **Alto Rendimiento** para la búsqueda de frases mnemónicas (BIP39) con saldo en las redes de Ethereum y Bitcoin.

A diferencia de los scripts convencionales, estas herramientas utilizan una **estrategia de búsqueda Offline** basada en **Filtros de Bloom** cargados en la memoria RAM, permitiendo velocidades de escaneo masivas sin depender de Internet.

---

## 🛠️ Arquitectura de Alto Nivel
*   **Escaneo Offline:** El script descarga la lista de todas las direcciones con saldo (Snapshot) y las indexa en la RAM. No se consulta la red a menos que haya un "Match" local.
*   **Multiprocesamiento:** Diseñado para utilizar todos los núcleos de tu CPU al 100%.
*   **Triple-Hit (BTC):** Prueba simultáneamente direcciones Legacy (1...), SegWit (3...) y Native SegWit (bc1...) para cada frase generada.

---

## 📁 Estructura del Repositorio

### 🔹 `/eth` (Ethereum Hunter)
*   `eth_hunter.py`: Motor profesional para Ethereum.
*   **Uso:** `python3 eth/eth_hunter.py`
*   **Funcionamiento:** Descarga automáticamente los 120 millones de direcciones con saldo de Blockchair y las indexa en RAM (~500MB).

### 🔹 `/btc` (Bitcoin Hunter)
*   `btc_hunter.py`: Motor profesional para Bitcoin.
*   **Uso:** `python3 btc/btc_hunter.py`
*   **Funcionamiento:** Descarga los 52 millones de direcciones con saldo de Bitcoin y prueba los formatos Legacy y Bech32 en cada semilla.

---

## 🚀 Guía de Inicio Rápido

1.  **Instalar dependencias:**
    ```bash
    pip install -r eth/requirements.txt
    pip install -r btc/requirements.txt
    ```

2.  **Lanzar el Cazador de Ethereum:**
    ```bash
    python3 eth/eth_hunter.py
    ```

3.  **Lanzar el Cazador de Bitcoin:**
    ```bash
    python3 btc/btc_hunter.py
    ```

---

## ⚠️ Requisitos de Hardware
*   **RAM:** Mínimo 4 GB disponibles para cargar los filtros de Bloom.
*   **CPU:** Mínimo 2 núcleos para aprovechar el multiprocesamiento.
*   **Disco:** Al menos 5 GB libres para los snapshots de las direcciones.

---

## 📜 Logs y Resultados
*   Si se encuentra un acierto, los datos (Frase, Dirección y Clave Privada) se guardarán automáticamente en archivos llamados `EXITOS_PRO.txt` o `BTC_SUCCESS.txt`.
*   Toda la actividad del sistema se puede monitorear en tiempo real en la terminal o mediante archivos `.log`.

*Desarrollado con arquitectura de ingeniería de alto nivel para maximizar las probabilidades de éxito.*
