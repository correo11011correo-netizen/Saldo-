import os
import hmac
import hashlib
import struct
import time
import requests
import mmh3
import gzip
import base58
import bech32
from tqdm import tqdm
from bitarray import bitarray
from ecdsa import SECP256k1, SigningKey
from mnemonic import Mnemonic
from multiprocessing import Process, cpu_count, Value

# ============================
#   BTC BLOOM FILTER (52M)
# ============================

class BloomFilter:
    def __init__(self, size=600000000, hashes=4): # ~80MB RAM
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
#   BTC SNAPSHOT LOADER
# ============================

BTC_URL = "https://gz.blockchair.com/bitcoin/addresses/blockchair_bitcoin_addresses_latest.tsv.gz"
BTC_GZ_FILE = "btc_addresses_latest.tsv.gz"

def load_btc_addresses(bf):
    # 1. Descargar con aria2c (Estilo IDM - Multi-hilo)
    if not os.path.exists(BTC_GZ_FILE):
        print("[*] Iniciando descarga acelerada de Bitcoin con aria2c (16 conexiones)...")
        import subprocess
        try:
            # -x16 (16 conexiones), -s16 (16 hilos)
            cmd = ["aria2c", "-x16", "-s16", "-k1M", "--console-log-level=warn", BTC_URL, "-o", BTC_GZ_FILE]
            subprocess.run(cmd, check=True)
        except Exception as e:
            print(f"❌ Error en descarga acelerada: {e}")
            # Fallback
            r = requests.get(BTC_URL, stream=True)
            with open(BTC_GZ_FILE, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
    
    print("\n[*] Indexando 52M de direcciones BTC en RAM...")
    with gzip.open(BTC_GZ_FILE, 'rt') as f:
        next(f)
        for line in tqdm(f, total=52000000, desc="Indexando BTC", unit="addr"):
            parts = line.split('\t')
            if len(parts) > 0:
                bf.add(parts[0]) # Direcciones BTC son case-sensitive o bech32

# ============================
#   BTC WALLET ENGINE (TRIPLE-HIT)
# ============================

mnemo = Mnemonic("english")

def sha256_ripe160(data):
    sha = hashlib.sha256(data).digest()
    ripe = hashlib.new('ripemd160', sha).digest()
    return ripe

def pubkey_to_legacy(pubkey): # 1...
    ripe = sha256_ripe160(pubkey)
    pre = b'\x00' + ripe
    checksum = hashlib.sha256(hashlib.sha256(pre).digest()).digest()[:4]
    return base58.b58encode(pre + checksum).decode()

def pubkey_to_bech32(pubkey): # bc1...
    ripe = sha256_ripe160(pubkey)
    return bech32.bech32_encode('bc', bech32.convertbits(ripe, 8, 5))

def generate_btc_wallets():
    mnemonic = mnemo.to_mnemonic(os.urandom(16))
    seed = hashlib.pbkdf2_hmac("sha512", mnemonic.encode("utf-8"), b"mnemonic", 2048, dklen=64)
    I = hmac.new(b"Bitcoin seed", seed, hashlib.sha512).digest()
    m_priv, m_chain = I[:32], I[32:]

    # Derivación básica m/44'/0'/0'/0/0 (Legacy)
    def derive(k, c, index):
        data = b"\x00" + k + struct.pack(">L", index + 0x80000000)
        I = hmac.new(c, data, hashlib.sha512).digest()
        return (int.from_bytes(I[:32], "big") + int.from_bytes(k, "big")) % SECP256k1.order, I[32:]

    k_int, c = derive(m_priv, m_chain, 44)
    k_int, c = derive(k_int.to_bytes(32, "big"), c, 0)
    
    sk = SigningKey.from_string(k_int.to_bytes(32, "big"), curve=SECP256k1)
    vk = sk.get_verifying_key()
    pub_comp = vk.to_string("compressed")
    
    # Generamos los 2 tipos principales por ahora (Legacy y Native SegWit)
    addr_legacy = pubkey_to_legacy(pub_comp)
    addr_bech32 = pubkey_to_bech32(pub_comp)
    
    return mnemonic, [addr_legacy, addr_bech32], k_int.to_bytes(32, "big").hex()

def worker(worker_id, bf, counter):
    while True:
        mnemonic, addrs, priv = generate_btc_wallets()
        for addr in addrs:
            if addr in bf:
                print(f"\n[!] MATCH BTC ENCONTRADO: {addr}")
                # Verificación de saldo (Simplificado, los pro guardan todo y verifican después)
                with open("BTC_SUCCESS.txt", "a") as f:
                    f.write(f"SEED: {mnemonic}\nADDR: {addr}\nPRIV: {priv}\n\n")
        
        with counter.get_lock():
            counter.value += 1
            if counter.value % 5000 == 0:
                print(f"[*] BTC Worker {worker_id}: {counter.value} seeds probadas.")

if __name__ == "__main__":
    bf = BloomFilter()
    load_btc_addresses(bf)
    
    shared_counter = Value('i', 0)
    num_cores = cpu_count()
    print(f"\n[*] MOTORES BTC LISTOS. Usando {num_cores} núcleos.")

    processes = []
    for i in range(num_cores):
        p = Process(target=worker, args=(i, bf, shared_counter))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()
