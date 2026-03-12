import time
import os
from web3 import Web3
from eth_account import Account

# ============================
#   CONFIGURACIÓN DE PRODUCCIÓN
# ============================

# 1. Cargar Credenciales y Contrato
with open("MEV_WALLET_SECRET.txt", "r") as f:
    content = f.read()
    MY_ADDR = content.split("ADDRESS: ")[1].split("\n")[0]
    MY_PRIV = content.split("PRIVATE_KEY: ")[1].split("\n")[0]

with open("CONTRACT_ADDRESS.txt", "r") as f:
    CONTRACT_ADDR = f.read().strip()

# 2. Conexión RPC Robusta
w3 = Web3(Web3.HTTPProvider("https://polygon-bor-rpc.publicnode.com"))

# 3. ABI Mínimo para llamar al contrato
ABI = [
    {
        "inputs": [{"name": "_token", "type": "address"}, {"name": "_amount", "type": "uint256"}],
        "name": "requestFlashLoan",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

def run_system_test():
    print(f"=== TEST DE COORDINACIÓN: SISTEMA MEV v5.0 ===")
    
    # TEST 1: Conexión
    if w3.is_connected():
        print(f"✅ [TEST 1/3] Conexión a Polygon OK.")
    else:
        print(f"❌ [TEST 1/3] Fallo de conexión.")
        return False

    # TEST 2: Saldo para Gas
    balance = w3.eth.get_balance(MY_ADDR)
    eth_bal = w3.from_wei(balance, "ether")
    print(f"✅ [TEST 2/3] Saldo de Gas: {eth_bal:.4f} POL.")
    if eth_bal < 0.1:
        print("⚠️ Alerta: Saldo bajo para operaciones continuas.")

    # TEST 3: Integridad del Contrato
    try:
        code = w3.eth.get_code(CONTRACT_ADDR)
        if len(code) > 2:
            print(f"✅ [TEST 3/3] Contrato detectado en {CONTRACT_ADDR}")
        else:
            print(f"❌ [TEST 3/3] No hay código en la dirección del contrato.")
            return False
    except Exception as e:
        print(f"❌ [TEST 3/3] Error verificando contrato: {e}")
        return False

    print(f"\n🚀 TODOS LOS SISTEMAS LISTOS. Iniciando motor de búsqueda...\n")
    return True

def start_hunting():
    if not run_system_test():
        return

    # Direcciones de tokens para arbitraje (USDC / DAI)
    USDC = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
    
    contract = w3.eth.contract(address=CONTRACT_ADDR, abi=ABI)

    while True:
        try:
            # --- LÓGICA DE DETECCIÓN (SIMULACIÓN DE OPORTUNIDAD REAL) ---
            print(f"[*] Buscando oportunidades en bloques de Polygon... ", end="\r")
            
            # Simulamos que encontramos una oportunidad del 0.5%
            oportunidad_detectada = False # Cambiar a True para ejecutar una real
            
            if oportunidad_detectada:
                print(f"\n🔥 ¡OPORTUNIDAD REAL DETECTADA! Llamando al contrato...")
                
                # Pedimos un Flash Loan de 1000 USDC
                nonce = w3.eth.get_transaction_count(MY_ADDR)
                tx = contract.functions.requestFlashLoan(USDC, w3.to_wei(1000, 'mwei')).build_transaction({
                    'chainId': 137,
                    'gas': 500000,
                    'gasPrice': w3.eth.gas_price,
                    'from': MY_ADDR,
                    'nonce': nonce,
                })
                
                signed_tx = w3.eth.account.sign_transaction(tx, private_key=MY_PRIV)
                tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                print(f"✅ Transacción de Arbitraje enviada: {tx_hash.hex()}")
                break # Detenemos tras la primera ejecución exitosa para seguridad del test

            time.sleep(2)
        except Exception as e:
            print(f"\n[!] Error en el motor: {e}")
            time.sleep(5)

if __name__ == "__main__":
    start_hunting()
