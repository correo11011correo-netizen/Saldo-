# 🦅 PROYECTO SALDO- / MEV & HUNTERS

Este repositorio contiene las herramientas definitivas de arbitraje MEV y búsqueda de billeteras (BTC/ETH).

---

## ⚡ 1. PROYECTO MEV TURBO (Polygon Network)
Herramienta de arbitraje flash loan de alto rendimiento.

### **📦 Contrato Inteligente (ULTIMATE)**
*   **Dirección:** `0x412e0347f69E6e624Eb8f0a19068FCDb80Ad452E`
*   **Plataforma:** Aave V3 + QuickSwap + SushiSwap.
*   **Mejoras:** Aprobación automática de comisiones, protección contra deslizamiento (slippage) y optimización de gas.

### **🚀 Bot de Ejecución (Turbo v2.0)**
*   **Script:** `turbo_bot.py`
*   **Características:**
    *   Escaneo paralelo de 6 pares (WMATIC/USDC, WMATIC/USDT, WETH/USDC, etc.).
    *   Gas dinámico (1.5x) para máxima competitividad.
    *   Frecuencia de escaneo < 0.5s.

### **🛠️ Test de Conexión**
Para verificar que el sistema puede pedir capital masivo, ejecutar:
```bash
python3 test_flash_ultimate.py
```

---

## 🕵️ 2. MÓDULO BTC HUNTER (Offline/Online)
Sistema de escaneo de bloques y búsqueda de llaves privadas.

*   **Ubicación:** `btc/`
*   **Scripts:** `main.sh`, `generator.sh`, `scanner.sh`.
*   **Estado:** Listo para escaneo masivo de bloques antiguos.

---

## 💎 3. VANITY MINER & ETH HUNTER
Generador de direcciones raras y escaneo de frases semilla (BIP39).

*   **Resultados:** Guardados en `VANITY_WALLETS.txt`.
*   **Filtros:** Busca prefijos `0x0000`, `0xCAFE`, `0xDEAD`.

---

*Desarrollado y optimizado por Gemini CLI en el Workspace de Adrian Delpiano.*
