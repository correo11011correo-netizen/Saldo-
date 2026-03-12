from web3 import Web3
from solcx import compile_standard, install_solc
import json

# 1. Configuración de Wallet
with open("MEV_WALLET_SECRET.txt", "r") as f:
    content = f.read()
    MY_ADDR = content.split("ADDRESS: ")[1].split("\n")[0]
    MY_PRIV = content.split("PRIVATE_KEY: ")[1].split("\n")[0]

# 2. Conexión a Polygon
w3 = Web3(Web3.HTTPProvider("https://polygon-bor-rpc.publicnode.com"))
chain_id = 137

# 3. Instalar Compilador Solidity
print("[*] Instalando Solc v0.8.10...")
install_solc("0.8.10")

# 4. Leer y Compilar Contrato
with open("FlashArb.sol", "r") as file:
    contract_file = file.read()

compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {"FlashArb.sol": {"content": contract_file}},
        "settings": {"outputSelection": {"*": {"*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]}}},
    },
    solc_version="0.8.10",
)

bytecode = compiled_sol["contracts"]["FlashArb.sol"]["FlashArb"]["evm"]["bytecode"]["object"]
abi = compiled_sol["contracts"]["FlashArb.sol"]["FlashArb"]["abi"]

# 5. Desplegar Contrato
FlashArb = w3.eth.contract(abi=abi, bytecode=bytecode)
nonce = w3.eth.get_transaction_count(MY_ADDR)

print(f"[*] Desplegando Contrato desde {MY_ADDR}...")
transaction = FlashArb.constructor().build_transaction({
    "chainId": chain_id, 
    "gasPrice": w3.eth.gas_price, 
    "from": MY_ADDR, 
    "nonce": nonce
})
signed_tx = w3.eth.account.sign_transaction(transaction, private_key=MY_PRIV)

try:
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"[*] Transacción enviada! Hash: {tx_hash.hex()}")
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"✅ CONTRATO DESPLEGADO EN: {tx_receipt.contractAddress}")
    
    # Guardar dirección del contrato para el bot
    with open("CONTRACT_ADDRESS.txt", "w") as f:
        f.write(tx_receipt.contractAddress)

except Exception as e:
    print(f"❌ Error al desplegar: {e}")
    print("⚠️ Posible causa: No tienes MATIC suficiente para pagar el gas de despliegue.")
