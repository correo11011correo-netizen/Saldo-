import os
import re
from eth_account import Account
from mnemonic import Mnemonic
from multiprocessing import Process, Value, cpu_count

# Habilitar funciones mnemónicas
Account.enable_unaudited_hdwallet_features()

# ============================
#   FILTRO DE RAREZAS EXTREMO
# ============================
# Buscamos patrones de 3 y 4 caracteres al inicio (después del 0x)
patterns = [
    # Números repetidos (4 veces)
    r'^0x0000', r'^0x1111', r'^0x2222', r'^0x3333', r'^0x4444', r'^0x5555', r'^0x6666', r'^0x7777', r'^0x8888', r'^0x9999',
    # Secuencias numéricas
    r'^0x1234', r'^0x4321', r'^0x007',
    # Palabras Inglés (Leet)
    r'^0xdead', r'^0xbeef', r'^0xcafe', r'^0xface', r'^0xace', r'^0xdeed', r'^0xfeed', r'^0xbad', r'^0xbabe', r'^0xcode',
    # Palabras Español (Leet)
    r'^0xfaca', r'^0xbaca', r'^0xfede', r'^0xbeba', r'^0xada', r'^0xbaba', r'^0xcaca', r'^0xdado', r'^0xbeso',
    # Letras repetidas
    r'^0xaaaa', r'^0xbbbb', r'^0xcccc', r'^0xdddd', r'^0xeeee', r'^0xffff'
]
COMBINED_PATTERN = re.compile('|'.join(patterns), re.IGNORECASE)

# ============================
#   MOTOR DE MINERÍA
# ============================

def vanity_worker(worker_id, counter):
    mnemo = Mnemonic("english")
    
    while True:
        # Generar 12 palabras (BIP39)
        entropy = os.urandom(16)
        phrase = mnemo.to_mnemonic(entropy)
        
        try:
            # Derivación ultrarrápida (MetaMask Standard)
            acct = Account.from_mnemonic(phrase)
            address = acct.address
            
            # FILTRO DE RAREZA
            if COMBINED_PATTERN.match(address):
                with open("VANITY_WALLETS.txt", "a") as f:
                    f.write(f"ADDRESS: {address}\n")
                    f.write(f"MNEMONIC: {phrase}\n")
                    f.write(f"PRIVATE_KEY: {acct.key.hex()}\n")
                    f.write("-" * 50 + "\n")
            
            # Contador de progreso (silencioso para background)
            with counter.get_lock():
                counter.value += 1
                    
        except Exception:
            continue

if __name__ == "__main__":
    shared_counter = Value('i', 0)
    num_cores = cpu_count()
    processes = []

    for i in range(num_cores):
        p = Process(target=vanity_worker, args=(i, shared_counter))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()
