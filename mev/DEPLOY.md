# 🚀 GUÍA DE DESPLIEGUE MEV v6.0 ULTRA-SWEEP

Sigue estos pasos para desplegar el bot en un nuevo servidor Linux (VPS).

### 1. Requisitos Previos
```bash
sudo apt update && sudo apt install python3-venv python3-pip -y
```

### 2. Configurar Entorno
```bash
python3 -m venv venv_eth
source venv_eth/bin/activate
pip install web3 py-solc-x
```

### 3. Configurar Secretos
Crea el archivo `MEV_WALLET_SECRET.txt` con este formato:
```text
ADDRESS: 0xTuDireccion
PRIVATE_KEY: TuLlavePrivada
MNEMONIC: TuFraseSemilla (Opcional)
```

### 4. Desplegar Contrato
Usa el script de despliegue incluido o compila `FlashArbULTIMATE.sol` en Remix. Pega la dirección en `CONTRACT_ADDRESS.txt`.

### 5. Lanzar el Bot
```bash
nohup python3 turbo_bot.py > /dev/null 2>&1 &
```

### 6. Monitorizar en Vivo
```bash
python3 monitor_mev.py
```
