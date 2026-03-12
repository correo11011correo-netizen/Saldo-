import os
import hmac
import hashlib
import struct
import time
import requests
import mmh3
import gzip
import shutil
from tqdm import tqdm
from bitarray import bitarray
from ecdsa import SECP256k1, SigningKey
from eth_hash.auto import keccak
from mnemonic import Mnemonic
from multiprocessing import Process, cpu_count, Value

# ============================
#   BLOOM FILTER CONFIG (120M)
# ============================

class BloomFilter:
    def __init__(self, size=800000000, hashes=4): # ~100MB RAM
        self.size = size
        self.hashes = hashes
        self.bit_array = bitarray(size)
        self.bit_array.setall(0)

    def add(self, string):
        for seed in range(self.hashes):
            result = mmh3.hash(string, seed) % self.size
            self.bit_array[result] = 1

    def __contains__(self, string):
        for seed in range(self.hashes):
            result = mmh3.hash(string, seed) % self.size
            if self.bit_array[result] == 0:
                return False
        return True

# ============================
#   ADRESS LIST DOWNLOADER
# ============================

ADDRESSES_URL = "https://gz.blockchair.com/ethereum/addresses/blockchair_ethereum_addresses_latest.tsv.gz"
LOCAL_GZ_FILE = "eth_addresses_latest.tsv.gz"

def load_all_addresses(bloom_filter):
    # 1. Descargar si no existe (Ahorramos ancho de banda)
    if not os.path.exists(LOCAL_GZ_FILE):
        print("[*] Descargando Snapshot de 120M de direcciones... (Esto puede tardar unos minutos)")
        r = requests.get(ADDRESSES_URL, stream=True)
        total_size = int(r.headers.get('content-length', 0))
        with open(LOCAL_GZ_FILE, 'wb') as f, tqdm(total=total_size, unit='B', unit_scale=True) as bar:
            for data in r.iter_content(chunk_size=1024*1024):
                f.write(data)
                bar.update(len(data))
    
    # 2. Cargar en Bloom Filter (Sin descomprimir a disco para no gastar espacio)
    print("\n[*] Cargando direcciones en la RAM... (Paciencia, son 120 millones)")
    with gzip.open(LOCAL_GZ_FILE, 'rt') as f:
        # Saltar la cabecera
        next(f)
        for line in tqdm(f, total=120000000, desc="Indexando en RAM", unit="addr"):
            parts = line.split('\t')
            if len(parts) > 0:
                bloom_filter.add(parts[0].lower())

# ============================
#   WORKER & WALLET ENGINE
# ============================

mnemo = Mnemonic("english")

def generate_eth_wallet():
    # Generación ultra-rápida (Simplificada)
    mnemonic = mnemo.to_mnemonic(os.urandom(16))
    seed = hashlib.pbkdf2_hmac("sha512", mnemonic.encode("utf-8"), b"mnemonic", 2048, dklen=64)
    I = hmac.new(b"Bitcoin seed", seed, hashlib.sha512).digest()
    m_priv, m_chain = I[:32], I[32:]
    
    # Derivación directa m/44'/60'/0'/0/0 (MetaMask)
    def derive(k, c, index):
        data = b"\x00" + k + struct.pack(">L", index + 0x80000000)
        I = hmac.new(c, data, hashlib.sha512).digest()
        return (int.from_bytes(I[:32], "big") + int.from_bytes(k, "big")) % SECP256k1.order, I[32:]

    k_int, c = derive(m_priv, m_chain, 44)
    k_int, c = derive(k_int.to_bytes(32, "big"), c, 60)
    k_int, c = derive(k_int.to_bytes(32, "big"), c, 0)
    
    # Solo generamos la dirección del índice 0
    sk = SigningKey.from_string(k_int.to_bytes(32, "big"), curve=SECP256k1)
    pub = b"\x04" + sk.get_verifying_key().to_string()
    addr = keccak(pub[1:])[-20:].hex().lower()
    return mnemonic, "0x" + addr, k_int.to_bytes(32, "big").hex()

def get_real_balance(address):
    # Solo consultamos internet si el filtro dice que hay saldo
    try:
        url = f"https://cloudflare-eth.com"
        payload = {"jsonrpc":"2.0","method":"eth_getBalance","params":[address, "latest"],"id":1}
        r = requests.post(url, json=payload, timeout=5)
        return int(r.json()["result"], 16)
    except: return -1

def worker(worker_id, bloom_filter, counter):
    while True:
        mnemonic, address, priv = generate_eth_wallet()
        
        # BUSQUEDA OFFLINE (RAM)
        if address in bloom_filter:
            print(f"\n[!] POSIBLE ACIERTO: {address} (Validando...)")
            balance = get_real_balance(address)
            if balance > 0:
                print(f"🔥 GANADOR: {address} -> {balance/10**18} ETH")
                with open("EXITOS_PRO.txt", "a") as f:
                    f.write(f"SEED: {mnemonic}\nADDR: {address}\nPRIV: {priv}\nBAL: {balance/10**18} ETH\n\n")
        
        with counter.get_lock():
            counter.value += 1
            if counter.value % 5000 == 0:
                print(f"[*] Proceso {worker_id}: {counter.value} seeds probadas.")

# ============================
#   MAIN
# ============================

if __name__ == "__main__":
    # 1. Crear el portero (Filtro de Bloom)
    # 800M bits = ~100 MB. Suficiente para 120M con baja tasa de error.
    bf = BloomFilter(size=800000000, hashes=4)
    
    # 2. Cargar las 120 millones de direcciones
    load_all_addresses(bf)
    
    # 3. Lanzar motores (2 núcleos)
    shared_counter = Value('i', 0)
    processes = []
    num_cores = cpu_count()
    print(f"\n[*] MOTORES LISTOS. Usando {num_cores} núcleos para escaneo Offline.")

    for i in range(num_cores):
        p = Process(target=worker, args=(i, bf, shared_counter))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()
