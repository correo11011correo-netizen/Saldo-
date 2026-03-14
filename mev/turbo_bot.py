import time, os, json
from web3 import Web3
from datetime import datetime
import concurrent.futures

# CONFIGURACIÓN PROFESIONAL
RPC = "https://polygon-bor-rpc.publicnode.com"
w3 = Web3(Web3.HTTPProvider(RPC))

with open("MEV_WALLET_SECRET.txt", "r") as f:
    content = f.read()
    MY_ADDR = content.split("ADDRESS: ")[1].split("\n")[0]
    MY_PRIV = content.split("PRIVATE_KEY: ")[1].split("\n")[0]

with open("CONTRACT_ADDRESS.txt", "r") as f:
    CONTRACT_ADDR = f.read().strip()

TOKENS = {
    "WMATIC": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
    "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
    "WETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
    "DAI": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063"
}
QUICK_ROUTER = "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff"
SUSHI_ROUTER = "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506"

ROUTER_ABI = [{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsOut","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"}]
CONTRACT_ABI = [{"inputs":[{"name":"_token","type":"address"},{"name":"_amount","type":"uint256"},{"name":"_targetToken","type":"address"}],"name":"requestFlashLoan","outputs":[],"stateMutability":"nonpayable","type":"function"}]

quick_c = w3.eth.contract(address=QUICK_ROUTER, abi=ROUTER_ABI)
sushi_c = w3.eth.contract(address=SUSHI_ROUTER, abi=ROUTER_ABI)
mev_c = w3.eth.contract(address=CONTRACT_ADDR, abi=CONTRACT_ABI)

def log_event(msg):
    with open("mev_pro.log", "a") as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")

def check_pair(base, target):
    b_addr, t_addr = TOKENS[base], TOKENS[target]
    amount_in = w3.to_wei(5000, 'ether') if base == "WMATIC" else w3.to_wei(5000, 'mwei')
    
    try:
        out_q = quick_c.functions.getAmountsOut(amount_in, [b_addr, t_addr]).call()[1]
        out_s = sushi_c.functions.getAmountsOut(out_q, [t_addr, b_addr]).call()[1]
        
        profit = out_s - amount_in
        
        # Guardar estadísticas para el monitor
        with open("stats.json", "w") as s:
            json.dump({"last_scan": f"{base}/{target}", "gas": w3.eth.gas_price / 10**9, "profit": float(w3.from_wei(profit, 'ether'))}, s)
        
        if profit > w3.to_wei(0.1, 'ether'):
            log_event(f"🚀 HIT DETECTADO: {base}/{target} | Profit: {w3.from_wei(profit, 'ether')} POL")
            nonce = w3.eth.get_transaction_count(MY_ADDR)
            tx = mev_c.functions.requestFlashLoan(b_addr, amount_in, t_addr).build_transaction({
                'chainId': 137, 'gas': 1200000, 'gasPrice': int(w3.eth.gas_price * 1.5), 'from': MY_ADDR, 'nonce': nonce
            })
            signed = w3.eth.account.sign_transaction(tx, MY_PRIV)
            tx_h = w3.eth.send_raw_transaction(signed.raw_transaction)
            with open("HITS_FOUND.txt", "a") as h:
                h.write(f"{datetime.now()}: TX {tx_h.hex()} | Pair {base}/{target}\n")
            return True
    except Exception as e:
        pass
    return False

def engine():
    pairs = [("WMATIC", "USDC"), ("WMATIC", "USDT"), ("WETH", "USDC"), ("USDC", "USDT"), ("WMATIC", "DAI")]
    log_event("SISTEMA INICIADO - Patrullando 5 pares principales.")
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
        while True:
            ex.map(lambda p: check_pair(*p), pairs)
            time.sleep(0.3)

if __name__ == "__main__":
    engine()
