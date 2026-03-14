import time, os, json
from web3 import Web3
from datetime import datetime
import concurrent.futures

# CONFIGURACIÓN PROFESIONAL v6.0 SWEEP + MONITOR
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

SWEEP_LEVELS = [200, 1000, 5000, 20000, 110000]

def log_event(msg):
    with open("mev_pro.log", "a") as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")

def check_best_amount(base, target):
    b_addr, t_addr = TOKENS[base], TOKENS[target]
    best_profit = -999
    best_amount = 0
    results = {}
    
    for level in SWEEP_LEVELS:
        dec = 18 if base in ["WMATIC", "WETH", "DAI"] else 6
        amount_in = w3.to_wei(level, 'ether') if dec == 18 else int(level * 10**6)
        
        try:
            out_q = quick_c.functions.getAmountsOut(amount_in, [b_addr, t_addr]).call()[1]
            out_s = sushi_c.functions.getAmountsOut(out_q, [t_addr, b_addr]).call()[1]
            profit = out_s - amount_in
            results[str(level)] = float(w3.from_wei(profit, 'ether'))
            
            if profit > best_profit:
                best_profit = profit
                best_amount = amount_in
        except: continue
    
    # Enviar datos al monitor
    with open("stats.json", "w") as s:
        json.dump({
            "pair": f"{base}/{target}",
            "gas": w3.eth.gas_price / 10**9,
            "levels": results,
            "best_profit": float(w3.from_wei(best_profit, 'ether')),
            "block": w3.eth.block_number,
            "time": datetime.now().strftime('%H:%M:%S')
        }, s)

    if best_profit > w3.to_wei(0.08, 'ether'):
        execute_strike(base, target, best_amount, best_profit)

def execute_strike(base, target, amount, profit):
    b_addr, t_addr = TOKENS[base], TOKENS[target]
    log_event(f"🎯 BARRIDO EXITOSO: {base}/{target} | Monto: {amount} | Profit: {w3.from_wei(profit, 'ether')} POL")
    nonce = w3.eth.get_transaction_count(MY_ADDR)
    tx = mev_c.functions.requestFlashLoan(b_addr, amount, t_addr).build_transaction({
        'chainId': 137, 'gas': 1500000, 'gasPrice': int(w3.eth.gas_price * 1.6), 'from': MY_ADDR, 'nonce': nonce
    })
    signed = w3.eth.account.sign_transaction(tx, MY_PRIV)
    tx_h = w3.eth.send_raw_transaction(signed.raw_transaction)
    with open("HITS_FOUND.txt", "a") as h:
        h.write(f"{datetime.now()}: STRIKE {tx_h.hex()} | Amount {amount} | Pair {base}/{target}\n")

def engine():
    pairs = [("WMATIC", "USDC"), ("WMATIC", "USDT"), ("WETH", "USDC"), ("USDC", "USDT"), ("WMATIC", "DAI")]
    while True:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
            ex.map(lambda p: check_best_amount(*p), pairs)
        time.sleep(0.1)

if __name__ == "__main__":
    engine()
