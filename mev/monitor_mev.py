import json, os, time
from web3 import Web3
from datetime import datetime

with open("MEV_WALLET_SECRET.txt", "r") as f:
    MY_ADDR = f.read().split("ADDRESS: ")[1].split("\n")[0]

RPC = "https://polygon-bor-rpc.publicnode.com"
w3 = Web3(Web3.HTTPProvider(RPC))

def draw():
    os.system('clear')
    print("="*65)
    print(f" 🦅 MEV COMMAND CENTER v3.0 | {datetime.now().strftime('%H:%M:%S')}")
    print("="*65)
    
    try:
        with open("stats.json", "r") as s:
            data = json.load(s)
            print(f" 🛰️  Último Escaneo: {data['last_scan']}")
            print(f" ⛽ Gas Red: {data['gas']:.1f} Gwei")
            color = "\033[92m" if data['profit'] > 0 else "\033[91m"
            print(f" 📊 Profit Potencial: {color}{data['profit']:.6f} POL\033[0m")
    except:
        print(" [!] Esperando datos del bot...")

    print("-" * 65)
    try:
        bal = w3.from_wei(w3.eth.get_balance(MY_ADDR), 'ether')
        print(f" 💰 Mi Saldo: {bal:.4f} POL")
    except: pass

    print("-" * 65)
    print(" 📜 ÚLTIMOS EVENTOS (mev_pro.log):")
    try:
        os.system("tail -n 5 mev_pro.log")
    except: pass
    
    print("-" * 65)
    print(" 🚀 HITS RECIENTES (HITS_FOUND.txt):")
    try:
        os.system("tail -n 3 HITS_FOUND.txt")
    except: pass
    print("="*65)
    print(" [Presiona Ctrl+C para salir del monitor - El bot seguirá corriendo]")

while True:
    draw()
    time.sleep(1)
