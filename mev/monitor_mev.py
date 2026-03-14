import json, os, time
from web3 import Web3
from datetime import datetime

with open("MEV_WALLET_SECRET.txt", "r") as f:
    MY_ADDR = f.read().split("ADDRESS: ")[1].split("\n")[0]

RPC = "https://polygon-bor-rpc.publicnode.com"
w3 = Web3(Web3.HTTPProvider(RPC))

def draw():
    os.system('clear')
    print("="*70)
    print(f" 🦅 MEV ULTRA-MONITOR v6.0 | SWEEP MODE ACTIVE | {datetime.now().strftime('%H:%M:%S')}")
    print("="*70)
    
    try:
        with open("stats.json", "r") as s:
            d = json.load(s)
            print(f" 🛰️  Par Actual: {d['pair']} | 📦 Bloque: {d['block']} | ⛽ Gas: {d['gas']:.1f} Gwei")
            print("-" * 70)
            print(f" 📊 BARRIDO DE CAPITAL (Profit Estimado en POL):")
            for lvl, prof in d['levels'].items():
                color = "\033[92m" if prof > 0.08 else ("\033[93m" if prof > 0 else "\033[91m")
                print(f"    ↳ Nivel ${lvl.ljust(6)}: {color}{prof:+.6f} POL\033[0m")
            
            print("-" * 70)
            best_color = "\033[92m" if d['best_profit'] > 0.08 else "\033[94m"
            print(f" 🚀 MEJOR PROFIT ACTUAL: {best_color}{d['best_profit']:+.6f} POL\033[0m")
    except:
        print(" [!] Sincronizando con el motor de barrido...")

    print("-" * 70)
    try:
        bal = w3.from_wei(w3.eth.get_balance(MY_ADDR), 'ether')
        print(f" 💰 Mi Saldo: {bal:.4f} POL")
    except: pass

    print("-" * 70)
    print(" 📜 ÚLTIMOS EVENTOS:")
    os.system("tail -n 3 mev_pro.log")
    print("="*70)

while True:
    draw()
    time.sleep(0.5)
