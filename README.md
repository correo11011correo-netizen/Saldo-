# 🚀 Crypto Empire Pro v6.0 (Offline Search & MEV Arbitrage)

Este repositorio contiene una suite de herramientas de **Nivel Ingeniero** para la generación de ingresos en la Blockchain.

---

## 📁 Estructura de la Suite

### 🔹 `/vanity` (Vanity Miner)
*   **Función:** Generador masivo de direcciones mnemónicas con patrones raros.
*   **Resultados:** Guarda en `VANITY_WALLETS.txt`.

### 🔹 `/mev` (MEV Arbitrage Pro)
*   **Función:** Bot de arbitraje de alta frecuencia usando **Flash Loans** (Aave V3).
*   **Capital Requerido:** $0 (Préstamos de hasta $1,000,000).
*   **Contrato:** `FlashArb.sol` (Desplegado en Polygon).

### 🔹 `/eth` & `/btc` (Offline Hunters)
*   **Función:** Motores de búsqueda basados en Filtros de Bloom para encontrar wallets con saldo.

---

## ⚡ Guía de Inicio MEV (Polygon)
1. **Despliegue:** `python3 mev/deploy.py` (Requiere ~1 MATIC para gas).
2. **Ejecución:** `python3 mev/real_bot.py`

---

## 📜 Seguridad y Logs
*   Los archivos de claves privadas (`MEV_WALLET_SECRET.txt`) están protegidos por `.gitignore` y **NUNCA** se subirán al repositorio público.
*   Todas las ganancias se envían automáticamente a la wallet configurada en el despliegue.

*Arquitectura de ingeniería de alto nivel diseñada para el máximo rendimiento.*
