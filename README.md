# Proyecto de Herramientas BTC y ETH

Este proyecto contiene una colección de scripts para la generación de direcciones de Bitcoin (BTC) y Ethereum (ETH), así como para la verificación de saldos en estas criptomonedas. Los scripts están organizados en subcarpetas `btc/` y `eth/` para facilitar su gestión.

## Estructura del Proyecto

```
new_project/
├── btc/
│   ├── btc_2009_batch50.py
│   ├── btc_check_parallel.sh
│   ├── btc_2009_keygen_and_check.py
│   ├── scan_xpub_movements.py
│   ├── btc_2009_keygen.py
│   ├── btc_balance_check.sh
│   ├── btc_check_from_file.sh
│   ├── wif_to_addr_mainnet.py
│   ├── wif_to_addr_testnet.py
│   └── requirements.txt
└── eth/
    ├── eth_bip39_hunter.py
    └── requirements.txt
```

## Configuración Inicial

Para utilizar los scripts, primero debe instalar las dependencias de Python.

1.  **Navegue a la carpeta del proyecto:**
    ```bash
    cd new_project
    ```

2.  **Instale las dependencias de Python para BTC:**
    ```bash
    cd btc
    pip3 install -r requirements.txt
    cd ..
    ```
    *   **Nota sobre `pip3 install`:** Si encuentra un error de "externally-managed-environment", puede probar con `sudo apt install python3-requests` (ya que `python3-ecdsa` ya fue instalado). La mejor práctica en Python es usar un entorno virtual para evitar conflictos con el sistema:
        ```bash
        python3 -m venv venv_btc
        source venv_btc/bin/activate
        pip install -r requirements.txt
        ```
        Para desactivar el entorno virtual: `deactivate`

3.  **Instale las dependencias de Python para ETH:**
    ```bash
    cd eth
    pip3 install -r requirements.txt
    cd ..
    ```
    *   **Nota sobre `pip3 install`:** Similar al caso de BTC, si hay un error, puede probar con `sudo apt install python3-requests python3-eth-hash`. O usar un entorno virtual:
        ```bash
        python3 -m venv venv_eth
        source venv_eth/bin/activate
        pip install -r requirements.txt
        ```
        Para desactivar el entorno virtual: `deactivate`

## Uso de los Scripts

### Scripts de BTC (en la carpeta `new_project/btc/`)

*   **`btc_2009_batch50.py`**:
    *   **Descripción:** Genera 50 claves privadas y direcciones BTC (P2PKH mainnet) en un lote.
    *   **Uso:**
        ```bash
        python3 btc_2009_batch50.py
        ```
    *   **Salida:** Crea/actualiza el archivo `btc_keys_50.txt` con las claves y direcciones generadas.

*   **`btc_check_parallel.sh`**:
    *   **Descripción:** Lee direcciones BTC de un archivo y verifica sus saldos utilizando la API de mempool.space de forma paralela (50 hilos).
    *   **Uso:**
        ```bash
        ./btc_check_parallel.sh btc_keys_50.txt
        ```
    *   **Salida:** Los resultados se guardan en `with_funds.txt` (direcciones con fondos) y `no_funds.txt` (direcciones sin fondos).

*   **`btc_2009_keygen_and_check.py`**:
    *   **Descripción:** Genera continuamente nuevas claves privadas y direcciones BTC, verificando sus saldos en tiempo real utilizando un sistema multi-RPC. Este script está diseñado para una "caza" de fondos.
    *   **Uso:**
        ```bash
        python3 btc_2009_keygen_and_check.py
        ```
    *   **Salida:** Registra la última dirección y saldo en `formulario.txt`. Si se encuentran fondos, se añadirán al archivo `with_funds.txt`.

*   **`scan_xpub_movements.py`**:
    *   **Descripción:** Deriva direcciones públicas a partir de un XPUB y verifica sus transacciones y saldos. Útil para carteras HD (Hierarchical Deterministic).
    *   **Uso:**
        ```bash
        python3 scan_xpub_movements.py <SU_XPUB> <CANTIDAD_DIRECCIONES>
        ```
    *   **Ejemplo:**
        ```bash
        python3 scan_xpub_movements.py xpub6... 50
        ```
        Reemplace `<SU_XPUB>` con su clave pública extendida y `<CANTIDAD_DIRECCIONES>` con el número de direcciones a escanear a partir del XPUB.

### Scripts de ETH (en la carpeta `new_project/eth/`)

*   **`eth_bip39_hunter.py`**:
    *   **Descripción:** Genera direcciones Ethereum a partir de una frase mnemónica BIP39 y verifica sus saldos utilizando múltiples proveedores RPC. Diseñado para una "caza" de fondos.
    *   **Uso:**
        ```bash
        python3 eth_bip39_hunter.py
        ```
    *   **Interacción:** El script le pedirá que ingrese su frase mnemónica de 12 palabras.
    *   **Salida:** Los fondos encontrados se registrarán en `eth_with_funds.txt` y `eth_found_wallets.txt`.

---
