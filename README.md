# 🚀 Crypto Hunter Pro v5.2 (Offline Search Engine)

Este repositorio contiene herramientas de **Alto Rendimiento** para la búsqueda de frases mnemónicas (BIP39) con saldo en las redes de Ethereum y Bitcoin, además de un generador de direcciones de vanidad.

---

## 📁 Estructura del Repositorio

### 🔹 `/eth` (Ethereum Hunter)
*   `eth_hunter.py`: Motor profesional para Ethereum.
*   **Uso:** `python3 eth/eth_hunter.py`
*   **Funcionamiento:** Descarga automáticamente los 120 millones de direcciones con saldo y las indexa en RAM (~500MB).

### 🔹 `/btc` (Bitcoin Hunter)
*   `btc_hunter.py`: Motor profesional para Bitcoin.
*   **Uso:** `python3 btc/btc_hunter.py`
*   **Funcionamiento:** Descarga los 52 millones de direcciones con saldo y prueba los formatos Legacy y Bech32 en cada semilla.

### 🔹 `/vanity` (Vanity Miner)
*   `vanity_miner.py`: Generador de direcciones mnemónicas "raras".
*   **Uso:** `python3 vanity/vanity_miner.py`
*   **Funcionamiento:** Busca patrones como `0x0000`, `0x1111`, `0xCAFE`, `0xBACA`, etc., y los guarda en `VANITY_WALLETS.txt`.

---

## 📜 Logs y Resultados
*   Si se encuentra un acierto, los datos se guardarán automáticamente en archivos llamados `GOLD_FUNDS.txt`, `BTC_SUCCESS.txt` o `VANITY_WALLETS.txt`.

*Desarrollado con arquitectura de ingeniería de alto nivel para maximizar las probabilidades de éxito.*
