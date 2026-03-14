from web3 import Web3
from solcx import compile_standard, install_solc
import os

# 1. Configuración de Wallet
with open("MEV_WALLET_SECRET.txt", "r") as f:
    content = f.read()
    MY_ADDR = content.split("ADDRESS: ")[1].split("\n")[0]
    MY_PRIV = content.split("PRIVATE_KEY: ")[1].split("\n")[0]

# 2. Conexión a Polygon
w3 = Web3(Web3.HTTPProvider("https://polygon-bor-rpc.publicnode.com"))

# 3. Compilar
install_solc("0.8.10")
with open("FlashArbPRO.sol", "r") as file:
    contract_file = file.read()

compiled_sol = compile_standard(
    {"language": "Solidity", "sources": {"FlashArbPRO.sol": {"content": contract_file}},
     "settings": {"outputSelection": {"*": {"*": ["abi", "evm.bytecode"]}}}},
    solc_version="0.8.10",
)

bytecode = compiled_sol["contracts"]["FlashArbPRO.sol"]["FlashArbPRO"]["evm"]["bytecode"]["object"]
abi = compiled_sol["contracts"]["FlashArbPRO.sol"]["FlashArbPRO"]["abi"]

# 4. Desplegar
FlashArb = w3.eth.contract(abi=abi, bytecode=bytecode)
nonce = w3.eth.get_transaction_count(MY_ADDR)
tx = FlashArb.constructor().build_transaction({"chainId": 137, "gasPrice": w3.eth.gas_price, "from": MY_ADDR, "nonce": nonce})
signed_tx = w3.eth.account.sign_transaction(tx, private_key=MY_PRIV)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

print(f"✅ CONTRATO PRO DESPLEGADO: {tx_receipt.contractAddress}")
with open("CONTRACT_ADDRESS.txt", "w") as f: f.write(tx_receipt.contractAddress)
